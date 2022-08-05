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


def perform_query(payload: PerformQueryPayload):
    # running setup of bcftools
    # TODO dynamically decide format (include biosamples)
    args = [
        'bcftools', 'query',
        '--regions', f'{payload.chrom}:{payload.position}-{payload.position+1}',
        '--format', '%POS\t%REF\t%ALT\t%INFO\t[%GT,]\t[%SAMPLE,]\n',
        payload.vcf_location
    ]
    print(' '.join(args))
    query_process = subprocess.Popen(args, stdout=subprocess.PIPE, cwd='/tmp', encoding='ascii')
    
    call_count = 0 
    all_alleles_count = 0
    sample_indices = set()
    sample_names = []
    exists = False

    # iterate through bcftools output
    for line in query_process.stdout:
        try:
            (pos, reference, all_alts, info_str, genotypes, samples) = line.split('\t')
        except ValueError as e:
            print(repr(line.split('\t')))
            raise e

        pos = int(pos)
        # Ensure each variant will only be found by one process
        if pos != payload.position or payload.reference_bases != reference:
            continue

        alts = all_alts.split(',')
        hit_indexes = [
                i for i, alt in enumerate(alts)
                if alt.upper() == payload.alternate_bases
        ]
        if not hit_indexes:
            continue
        # hit_indexes are of form [0, 1] for ALT A,GC

        # Look through INFO for AC and AN, used for efficient calculations. Note
        # we cannot request them explicitly in the query, as bcftools will crash
        # if they aren't present.
        all_alt_counts = None
        total_count = None
        all_calls = None

        for info in info_str.split(';'):
            if info.startswith('AC='):
                all_alt_counts = info[3:]
            elif info.startswith('AN='):
                total_count = int(info[3:])

        # if AC=X was there
        if all_alt_counts is not None:
            alt_counts = [int(c) for c in all_alt_counts.split(',')]
            call_counts = [alt_counts[i] for i in hit_indexes]
            call_count += sum(call_counts)
        # otherwise
        else:
            # Much slower, but doesn't require INFO/AC
            # parsing 0|0,0|0,0|0,0|0
            all_calls = [int(g) for g in get_all_calls(genotypes)]
            hit_set = {i + 1 for i in hit_indexes}
            call_count += sum(1 for call in all_calls if call in hit_set)

        # if there are actual variants
        if call_count:
            exists = True
            hit_string = '|'.join(str(i + 1) for i in hit_indexes)
            pattern = re.compile(f'(^|[|/])({hit_string})([|/]|$)')
            
            if payload.requested_granularity in ('record', 'aggregated'):
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


    # TODO
    # if requested_granularity in ('record', 'aggregated'):
    #     args = [
    #         'bcftools', 'query',
    #         '--list-samples',
    #         vcf_location
    #     ]
    #     samples_process = subprocess.Popen(args, stdout=subprocess.PIPE, cwd='/tmp', encoding='ascii')
    #     sample_names = [line.strip() for n, line in enumerate(samples_process.stdout) if n in sample_indices]
    #     samples_process.stdout.close()

    return {
        'exists': exists,
        'all_alleles_count': all_alleles_count,
        'call_count': call_count,
        # TODO
        # 'sample_indices': list(sample_indices),
        # 'sample_names': sample_names
    }
