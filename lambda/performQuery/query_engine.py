import os
import re
import subprocess

import boto3

from shared.apiutils.requests import Granularity
from query_builder import QueryBuiler


# uncomment below for debugging
# os.environ['LD_DEBUG'] = 'all'
all_count_pattern = re.compile("[0-9]+")
get_all_calls = all_count_pattern.findall
s3 = boto3.client("s3")


def perform_query(payload: dict(), is_async: bool = False):
    region = payload["region"]
    variant_type = payload.get("variant_type", "")
    variant_prefix = f"<{variant_type}"

    ## region is of form: "chrom:start-end"
    first_base_pos = int(region[region.find(":") + 1 : region.find("-")])
    last_base_pos = int(region[region.find("-") + 1 :])
    chromosome = region[: region.find(":")]
    # alleles requested
    reference_bases = payload.get("reference_bases", "N")
    alternate_bases = payload.get("alternate_bases", "N")
    # variant end range
    end_min = payload["end_min"]
    end_max = payload["end_max"]
    # variant length
    variant_max_length = payload.get("variant_max_length", -1)
    variant_min_length = payload.get("variant_min_length", 0)

    if variant_max_length < 0:
        variant_max_length = float("inf")

    # granularity
    requested_granularity = payload.get("requested_granularity", Granularity.BOOLEAN)
    # details
    include_details = payload.get("include_details", False)
    chosen_samples = payload.get("samples", [])
    # samples
    include_samples = payload.get("include_samples", False)
    # query id
    query_id = payload.get("query_id", "-")
    dataset_id = payload.get("dataset_id", "-")

    # pipeline variables
    exists = False
    variants = []
    call_count = 0
    all_alleles_count = 0
    sample_indices = set()
    all_sample_names = []
    sample_names = []
    
    bcftools_query = QueryBuiler()
    bcftools_query = bcftools_query.set_samples(chosen_samples)
    bcftools_query = bcftools_query.set_region(region)
    bcftools_query = bcftools_query.set_return_samples(include_samples)

    bcftools_query = bcftools_query.set_vcf(payload["vcf_location"])
    args = bcftools_query.build()
    
    print("Iterating bcftools result")
    query_process = subprocess.Popen(
        args, stdout=subprocess.PIPE, cwd="/tmp", encoding="ascii"
    )
    
    # iterate through bcftools output
    for line in query_process.stdout:
        try:
            (
                vcf_position,
                vcf_reference,
                vcf_all_alts,
                vcf_info_str,
                vcf_genotypes,
                vcf_samples,
            ) = bcftools_query.parse_line(line)

            if not all_sample_names and vcf_samples:
                all_sample_names = [
                    sample for sample in vcf_samples.strip().strip(",").split(",")
                ]
        except ValueError as e:
            print(repr(line.split("\t")))
            raise e

        vcf_position = int(vcf_position)
        # Ensure each variant will only be found by one process
        # TODO handle CNVs
        if not first_base_pos <= vcf_position <= last_base_pos:
            continue

        vcf_reference_length = len(vcf_reference)

        # must be within end range
        # TODO this seems to be incorrect
        # if not end_min <= vcf_position + vcf_reference_length - 1 <= end_max:
        #     continue

        # validation; if not N validate
        if vcf_reference.upper() != reference_bases and reference_bases != "N":
            continue

        vcf_all_alts = vcf_all_alts.split(",")

        # alternate base not defined
        if alternate_bases == "N" and variant_type is not None:
            if variant_type == "DEL":
                hit_indexes = [
                    i
                    for i, alt in enumerate(vcf_all_alts)
                    if (
                        (alt.startswith(variant_prefix) or alt == "<CN0>")
                        if alt.startswith("<")
                        else len(alt) < vcf_reference_length
                    )
                    and variant_min_length <= len(alt) <= variant_max_length
                ]
            elif variant_type == "INS":
                hit_indexes = [
                    i
                    for i, alt in enumerate(vcf_all_alts)
                    if (
                        alt.startswith(variant_prefix)
                        if alt.startswith("<")
                        else len(alt) > vcf_reference_length
                    )
                    and variant_min_length <= len(alt) <= variant_max_length
                ]
            elif variant_type == "DUP":
                pattern = re.compile("({}){{2,}}".format(vcf_reference))
                hit_indexes = [
                    i
                    for i, alt in enumerate(vcf_all_alts)
                    if (
                        (
                            alt.startswith(variant_prefix)
                            or (alt.startswith("<CN") and alt not in ("<CN0>", "<CN1>"))
                        )
                        if alt.startswith("<")
                        else pattern.fullmatch(alt)
                    )
                    and variant_min_length <= len(alt) <= variant_max_length
                ]
            elif variant_type == "DUP:TANDEM":
                tandem = vcf_reference + vcf_reference
                hit_indexes = [
                    i
                    for i, alt in enumerate(vcf_all_alts)
                    if (
                        (alt.startswith(variant_prefix) or alt == "<CN2>")
                        if alt.startswith("<")
                        else alt == tandem
                    )
                    and variant_min_length <= len(alt) <= variant_max_length
                ]
            elif variant_type == "CNV":
                pattern = re.compile("\.|({})*".format(vcf_reference))
                hit_indexes = [
                    i
                    for i, alt in enumerate(vcf_all_alts)
                    if (
                        (
                            alt.startswith(variant_prefix)
                            or alt.startswith("<CN")
                            or alt.startswith("<DEL")
                            or alt.startswith("<DUP")
                        )
                        if alt.startswith("<")
                        else pattern.fullmatch(alt)
                    )
                    and variant_min_length <= len(alt) <= variant_max_length
                ]
            else:
                # For structural variants that aren't otherwise recognisable
                hit_indexes = [
                    i
                    for i, alt in enumerate(vcf_all_alts)
                    if alt.startswith(variant_prefix)
                    and variant_min_length <= len(alt) <= variant_max_length
                ]
        # if alternate base defined
        # here we should check for the asked variant lengths
        elif alternate_bases == "N":
            hit_indexes = [
                i
                for i, alt in enumerate(vcf_all_alts)
                if variant_min_length <= len(alt) <= variant_max_length
            ]
        else:
            hit_indexes = [
                i
                for i, alt in enumerate(vcf_all_alts)
                if alt.upper() == alternate_bases
                and variant_min_length <= len(alt) <= variant_max_length
            ]

        if not hit_indexes:
            continue
        # hit_indexes are of form [0, 1] for ALT A,GC

        # Look through INFO for AC and AN, used for efficient calculations. Note
        # we cannot request them explicitly in the query, as bcftools will crash
        # if they aren't present.
        all_alt_counts = None
        total_count = None
        vcf_variant_type = "N/A"

        for info in vcf_info_str.split(";"):
            if info.startswith("AC="):
                all_alt_counts = info[3:]
            elif info.startswith("AN="):
                total_count = int(info[3:])
            elif info.startswith("VT="):
                vcf_variant_type = info[3:]

        all_calls = None
        # if AC=X was there
        if all_alt_counts is not None:
            alt_counts = [int(c) for c in all_alt_counts.split(",")]
            call_counts = [alt_counts[i] for i in hit_indexes]
            # ["Chr1 123 A G SNP"]
            variants += [
                f"{chromosome}\t{vcf_position}\t{vcf_reference}\t{vcf_all_alts[i]}\t{vcf_variant_type}"
                for i in hit_indexes
                if alt_counts[i] != 0
            ]
            call_count += sum(call_counts)
        # otherwise
        else:
            # Much slower, but doesn't require INFO/AC
            # parsing 0|0,0|0,0|0,0|0
            all_calls = [int(g) for g in get_all_calls(vcf_genotypes)]
            hit_set = {i + 1 for i in hit_indexes}
            # ["Chr1 123 A G SNP"]
            variants += [
                f"{chromosome}\t{vcf_position}\t{vcf_reference}\t{vcf_all_alts[i-1]}\t{vcf_variant_type}"
                for i in set(all_calls) & hit_set
            ]
            call_count += sum(1 for call in all_calls if call in hit_set)

        # if there are actual variants
        if call_count:
            exists = True
            if not include_details:
                break
            hit_string = "|".join(str(i + 1) for i in hit_indexes)
            pattern = re.compile(f"(^|[|/])({hit_string})([|/]|$)")
            if requested_granularity == Granularity.RECORD and include_samples:
                sample_indices.update(
                    [
                        i
                        for i, gt in enumerate(vcf_genotypes.split(","))
                        if pattern.search(gt)
                    ]
                )

        # Used for calculating frequency. This will be a misleading value if the
        # alleles are spread over multiple vcf records. Ideally we should
        # return a dictionary for each matching record/allele, but for now the
        # beacon specification doesn't support it. A quick fix might be to
        # represent the frequency of any matching allele in the population of
        # haplotypes, but this could lead to an illegal value > 1.
        if total_count is not None:
            all_alleles_count += total_count
        else:
            # Much slower, but doesn't require INFO/AN
            if all_calls is None:
                all_calls = get_all_calls(vcf_genotypes)
            all_alleles_count += len(all_calls)

        # if only bool is asked and a variant if found
        if requested_granularity == Granularity.BOOLEAN and exists:
            break
    query_process.stdout.close()

    if requested_granularity == Granularity.RECORD and include_samples:
        sample_names = [
            sample for n, sample in enumerate(all_sample_names) if n in sample_indices
        ]

    print("Iterating bcftools result complete")

    response = {
        "dataset_id": dataset_id,
        "exists": exists,
        "all_alleles_count": all_alleles_count,
        "variants": variants,
        "call_count": call_count,
        "sample_names": [] if not include_samples else sample_names,
    }

    return response
