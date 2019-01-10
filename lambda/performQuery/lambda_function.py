import json
import os
import re
import subprocess

os.environ['PATH'] += ':' + os.environ['LAMBDA_TASK_ROOT']

BASES = [
    'A',
    'C',
    'G',
    'T',
    'N',
]


def perform_query(reference_bases, region, end_min, end_max, alternate_bases,
                  variant_type, include_details, vcf_location):
    args = [
        'bcftools', 'query',
        '--regions', region,
        '--format', '%POS\t%REF\t%ALT\t%INFO/AC\t%INFO/AN\t[%GT,]\n',
        vcf_location
    ]
    query_process = subprocess.Popen(args, stdout=subprocess.PIPE, cwd='/tmp',
                                     encoding='ascii')
    v_prefix = '<{}'.format(variant_type)
    first_bp = int(region[region.find(':')+1: region.find('-')])
    last_bp = int(region[region.find('-')+1:])
    approx = reference_bases == 'N'
    exists = False
    variant_count = 0
    call_count = 0
    all_alleles_count = 0
    sample_indexes = []
    for line in query_process.stdout:
        try:
            (position, reference, all_alts, all_alt_counts, total_count,
             genotypes) = line.split('\t')
        except ValueError as e:
            print(repr(line.split('\t')))
            raise e

        ref_length = len(reference)

        pos = int(position)
        # Ensure each variant will only be found by one process
        if not first_bp <= pos <= last_bp:
            continue

        if not end_min <= pos + ref_length - 1 <= end_max:
            continue

        if not approx and reference.upper() != reference_bases:
            continue

        alts = all_alts.split(',')
        if alternate_bases is None:
            if variant_type == 'DEL':
                hit_indexes = [i for i, alt in enumerate(alts)
                               if ((alt.startswith(v_prefix)
                                    or alt == '<CN0>')
                                   if alt.startswith('<')
                                   else len(alt) < ref_length)]
            elif variant_type == 'INS':
                hit_indexes = [i for i, alt in enumerate(alts)
                               if (alt.startswith(v_prefix)
                                   if alt.startswith('<')
                                   else len(alt) > ref_length)]
            elif variant_type == 'DUP':
                pattern = re.compile('({}){{2,}}'.format(reference))
                hit_indexes = [i for i, alt in enumerate(alts)
                               if ((alt.startswith(v_prefix)
                                    or (alt.startswith('<CN')
                                        and alt not in ('<CN0>', '<CN1>')))
                                   if alt.startswith('<')
                                   else pattern.fullmatch(alt))]
            elif variant_type == 'DUP:TANDEM':
                tandem = reference + reference
                hit_indexes = [i for i, alt in enumerate(alts)
                               if ((alt.startswith(v_prefix)
                                    or alt == '<CN2>')
                                   if alt.startswith('<')
                                   else alt == tandem)]
            elif variant_type == 'CNV':
                pattern = re.compile('\.|({})*'.format(reference))
                hit_indexes = [i for i, alt in enumerate(alts)
                               if ((alt.startswith(v_prefix)
                                    or alt.startswith('<CN')
                                    or alt.startswith('<DEL')
                                    or alt.startswith('<DUP'))
                                   if alt.startswith('<')
                                   else pattern.fullmatch(alt))]
            else:
                # For structural variants that aren't otherwise recognisable
                hit_indexes = [i for i, alt in enumerate(alts)
                               if alt.startswith(v_prefix)]
        else:
            if alternate_bases == 'N':
                hit_indexes = [i for i, alt in enumerate(alts)
                               if alt.upper() in BASES]
            else:
                hit_indexes = [i for i, alt in enumerate(alts)
                               if alt.upper() == alternate_bases]
        if not hit_indexes:
            continue

        alt_counts = all_alt_counts.split(',')
        call_counts = [int(alt_counts[i]) for i in hit_indexes]
        call_count += sum(call_counts)
        if call_count:
            if not exists:
                exists = True
                if not include_details:
                    break
            variant_count += sum(1 for i in call_counts if i)
            pattern = re.compile('(^|[|/])({})([|/]|$)'.format('|'.join(str(
                i for i in hit_indexes))))
            sample_indexes += [i for i, gt in enumerate(genotypes.split(','))
                               if pattern.search(gt)]
        # Used for calculating frequency. This will be a misleading value if the
        #  alleles are spread over multiple vcf records. Ideally we should
        #  return a dictionary for each matching record/allele, but for now the
        #  beacon specification doesn't support it. A quick fix might be to
        #  represent the frequency of any matching allele in the population of
        #  haplotypes, but this could lead to an illegal value > 1.
        all_alleles_count += int(total_count)
    query_process.stdout.close()
    samples = list(set(sample_indexes))
    return {
        'exists': exists,
        'all_alleles_count': all_alleles_count,
        'variant_count': variant_count,
        'call_count': call_count,
        'samples': samples,
    }


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    reference_bases = event['reference_bases']
    region = event['region']
    end_min = event['end_min']
    end_max = event['end_max']
    alternate_bases = event['alternate_bases']
    variant_type = event['variant_type']
    include_details = event['include_details']
    vcf_location = event['vcf_location']
    response = perform_query(reference_bases, region, end_min, end_max,
                             alternate_bases, variant_type, include_details,
                             vcf_location)
    print('Returning response: {}'.format(json.dumps(response)))
    return response
