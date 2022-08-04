import re
import subprocess

from lambda_payloads import PerformQueryPayload
# uncomment below for debugging
# os.environ['LD_DEBUG'] = 'all'

BASES = [
    'A',
    'C',
    'G',
    'T',
    'N',
]

all_count_pattern = re.compile('[0-9]+')
get_all_calls = all_count_pattern.findall


def perform_query(performQueryPayload: PerformQueryPayload):
    '''
    :param requested_granularity: one of "boolean", "count", "aggregated", "record"
    '''
    # running setup of bcftools
    args = [
        'bcftools', 'query',
        '--regions', performQueryPayload.region,
        '--format', '%POS\t%REF\t%ALT\t%INFO\t[%GT,]\t[%SAMPLE,]\n',
        performQueryPayload.vcf_location
    ]
    query_process = subprocess.Popen(args, stdout=subprocess.PIPE, cwd='/tmp', encoding='ascii')
    v_prefix = '<{}'.format(performQueryPayload.variant_type)
    # region is of form: "chrom:start-end"
    first_bp = int(performQueryPayload.region[performQueryPayload.region.find(':') + 1: performQueryPayload.region.find('-')])
    last_bp = int(performQueryPayload.region[performQueryPayload.region.find('-') + 1:])
    chrom = performQueryPayload.region[:performQueryPayload.region.find(':')]
    approx = performQueryPayload.reference_bases == 'N'
    exists = False
    variants = []
    call_count = 0
    all_alleles_count = 0
    sample_indices = set()
    sample_names = []
    variant_max_length = float('inf') if performQueryPayload.variant_max_length < 0 else performQueryPayload.variant_max_length

    # iterate through bcftools output
    for line in query_process.stdout:
        try:
            (position, reference, all_alts, info_str, genotypes, samples) = line.split('\t')
        except ValueError as e:
            print(repr(line.split('\t')))
            raise e

        pos = int(position)
        # Ensure each variant will only be found by one process
        if not first_bp <= pos <= last_bp:
            continue

        ref_length = len(reference)

        # must be within end range
        if not performQueryPayload.end_min <= pos + ref_length - 1 <= performQueryPayload.end_max:
            continue

        # validation; if not N validate regex
        if not approx:
            rgx = re.compile('^' + performQueryPayload.reference_bases.replace('N', '[ACGTN]{1}') + '$')
            if not rgx.match(reference.upper()):
                continue

        alts = all_alts.split(',')

        # alternate base not defined
        if performQueryPayload.alternate_bases is None:
            if variant_type == 'DEL':
                hit_indexes = [
                    i for i, alt in enumerate(alts)
                    if (
                        (alt.startswith(v_prefix) or alt == '<CN0>')
                        if alt.startswith('<')
                        else len(alt) < ref_length
                    )
                    and 
                    performQueryPayload.variant_min_length <= len(alt) <= variant_max_length
                ]
            elif variant_type == 'INS':
                hit_indexes = [
                    i for i, alt in enumerate(alts)
                    if (
                        alt.startswith(v_prefix)
                        if alt.startswith('<')
                        else len(alt) > ref_length
                    )
                    and 
                    performQueryPayload.variant_min_length <= len(alt) <= variant_max_length
                ]
            elif variant_type == 'DUP':
                pattern = re.compile('({}){{2,}}'.format(reference))
                hit_indexes = [
                    i for i, alt in enumerate(alts)
                    if (
                        (alt.startswith(v_prefix) or (alt.startswith('<CN') and alt not in ('<CN0>', '<CN1>')))
                        if alt.startswith('<') else pattern.fullmatch(alt)
                    )
                    and 
                    performQueryPayload.variant_min_length <= len(alt) <= variant_max_length
                ]
            elif variant_type == 'DUP:TANDEM':
                tandem = reference + reference
                hit_indexes = [
                    i for i, alt in enumerate(alts)
                    if (
                        (alt.startswith(v_prefix) or alt == '<CN2>') 
                        if alt.startswith('<') else alt == tandem
                    )
                    and 
                    performQueryPayload.variant_min_length <= len(alt) <= variant_max_length
                ]
            elif variant_type == 'CNV':
                pattern = re.compile('\.|({})*'.format(reference))
                hit_indexes = [
                    i for i, alt in enumerate(alts)
                    if (
                        (alt.startswith(v_prefix)
                            or alt.startswith('<CN')
                            or alt.startswith('<DEL')
                            or alt.startswith('<DUP')
                        ) if alt.startswith('<')  else pattern.fullmatch(alt)
                    )
                    and 
                    performQueryPayload.variant_min_length <= len(alt) <= variant_max_length
                ]
            else:
                # For structural variants that aren't otherwise recognisable
                hit_indexes = [
                    i for i, alt in enumerate(alts)
                    if alt.startswith(v_prefix)
                    and 
                    performQueryPayload.variant_min_length <= len(alt) <= variant_max_length
                ]
        # if alternate base defined
        # here we should check for the asked variant lengths
        else:
            if performQueryPayload.alternate_bases == 'N':
                hit_indexes = [
                    i for i, alt in enumerate(alts)
                    if alt.upper() in BASES 
                    and 
                    performQueryPayload.variant_min_length <= len(alt) <= variant_max_length
                ]
            else:
                hit_indexes = [
                    i for i, alt in enumerate(alts)
                    if alt.upper() == performQueryPayload.alternate_bases
                    and 
                    performQueryPayload.variant_min_length <= len(alt) <= variant_max_length
                ]
        if not hit_indexes:
            continue
        # hit_indexes are of form [0, 1] for ALT A,GC

        # Look through INFO for AC and AN, used for efficient calculations. Note
        # we cannot request them explicitly in the query, as bcftools will crash
        # if they aren't present.
        all_alt_counts = None
        total_count = None
        variant_type = 'N/A'

        for info in info_str.split(';'):
            if info.startswith('AC='):
                all_alt_counts = info[3:]
            elif info.startswith('AN='):
                total_count = int(info[3:])
            elif info.startswith('VT='):
                variant_type = info[3:]

        all_calls = None
        # if AC=X was there
        if all_alt_counts is not None:
            alt_counts = [int(c) for c in all_alt_counts.split(',')]
            call_counts = [alt_counts[i] for i in hit_indexes]
            # ["Chr1 123 A G SNP"]
            variants += [
                f'{chrom}\t{position}\t{reference}\t{alts[i]}\t{variant_type}'
                for i in hit_indexes 
                if alt_counts[i] != 0
            ]
            call_count += sum(call_counts)
        # otherwise
        else:
            # Much slower, but doesn't require INFO/AC
            # parsing 0|0,0|0,0|0,0|0
            all_calls = [int(g) for g in get_all_calls(genotypes)]
            hit_set = {i + 1 for i in hit_indexes}
            # ["Chr1 123 A G SNP"]
            variants += [
                f'{chrom}\t{position}\t{reference}\t{alts[i]}\t{variant_type}'
                for i in set(all_calls) & hit_set
            ]
            call_count += sum(1 for call in all_calls if call in hit_set)

        # if there are actual variants
        if call_count:
            exists = True
            if not performQueryPayload.include_details:
                break
            hit_string = '|'.join(str(i + 1) for i in hit_indexes)
            pattern = re.compile(f'(^|[|/])({hit_string})([|/]|$)')
            if performQueryPayload.requested_granularity in ('record', 'aggregated'):
                sample_indices.update([i for i, gt in enumerate(genotypes.split(',')) if pattern.search(gt)])
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
                all_calls = get_all_calls(genotypes)
            all_alleles_count += len(all_calls)
    query_process.stdout.close()


    if performQueryPayload.requested_granularity in ('record', 'aggregated'):
        args = [
            'bcftools', 'query',
            '--list-samples',
            performQueryPayload.vcf_location
        ]
        samples_process = subprocess.Popen(args, stdout=subprocess.PIPE, cwd='/tmp', encoding='ascii')
        sample_names = [line.strip() for n, line in enumerate(samples_process.stdout) if n in sample_indices]
        samples_process.stdout.close()

    return {
        'exists': exists,
        'all_alleles_count': all_alleles_count,
        'variants': variants,
        'call_count': call_count,
        'sample_indices': list(sample_indices),
        'sample_names': sample_names
    }
