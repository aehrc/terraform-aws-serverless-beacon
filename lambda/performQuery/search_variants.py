import os
import re
import subprocess
from uuid import uuid4
import boto3
from botocore.exceptions import ClientError
import time

from payloads.lambda_payloads import PerformQueryPayload
from payloads.lambda_responses import PerformQueryResponse
import dynamodb.variant_queries as db


# uncomment below for debugging
# os.environ['LD_DEBUG'] = 'all'
VARIANTS_BUCKET = os.environ['VARIANTS_BUCKET']


BASES = [
    'A',
    'C',
    'G',
    'T',
    'N',
]

all_count_pattern = re.compile('[0-9]+')
get_all_calls = all_count_pattern.findall
s3 = boto3.client('s3')


def perform_query(payload: PerformQueryPayload):
    '''
    :param requested_granularity: one of "boolean", "count", "aggregated", "record"
    '''
    # running setup of bcftools
    args = [
        'bcftools', 'query',
        '--regions', payload.region,
        '--format', '%POS\t%REF\t%ALT\t%INFO\t[%GT,]\n',
        # '--format', '%POS\t%REF\t%ALT\t%INFO\t[%GT,]\t[%SAMPLE,]\n',
        payload.vcf_location
    ]
    print(repr('CMD: ' + ' '.join(args[:5] + [repr(args[5])] + args[6:])))

    query_process = subprocess.Popen(args, stdout=subprocess.PIPE, cwd='/tmp', encoding='ascii')
    v_prefix = '<{}'.format(payload.variant_type)
    # region is of form: "chrom:start-end"
    first_bp = int(payload.region[payload.region.find(':') + 1: payload.region.find('-')])
    last_bp = int(payload.region[payload.region.find('-') + 1:])
    chrom = payload.region[:payload.region.find(':')]
    approx = payload.reference_bases == 'N'
    exists = False
    variants = []
    call_count = 0
    all_alleles_count = 0
    # sample_indices = set()
    # all_sample_names = []
    # sample_names = []
    variant_max_length = float('inf') if payload.variant_max_length < 0 else payload.variant_max_length

    # iterate through bcftools output
    for line in query_process.stdout:
        try:
            # (position, reference, all_alts, info_str, genotypes, samples) = line.split('\t')
            (position, reference, all_alts, info_str, genotypes) = line.split('\t')
            # if len(all_sample_names) == 0:
            #     all_sample_names = [sample for sample in samples.strip().strip(',').split(',')]
        except ValueError as e:
            print(repr(line.split('\t')))
            raise e

        pos = int(position)
        # Ensure each variant will only be found by one process
        if not first_bp <= pos <= last_bp:
            continue

        ref_length = len(reference)

        # must be within end range
        if not payload.end_min <= pos + ref_length - 1 <= payload.end_max:
            continue

        # validation; if not N validate regex
        if not approx:
            rgx = re.compile('^' + payload.reference_bases.replace('N', '[ACGTN]{1}') + '$')
            if not rgx.match(reference.upper()):
                continue

        alts = all_alts.split(',')

        # alternate base not defined
        if payload.alternate_bases is None:
            if variant_type == 'DEL':
                hit_indexes = [
                    i for i, alt in enumerate(alts)
                    if (
                        (alt.startswith(v_prefix) or alt == '<CN0>')
                        if alt.startswith('<')
                        else len(alt) < ref_length
                    )
                    and 
                    payload.variant_min_length <= len(alt) <= variant_max_length
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
                    payload.variant_min_length <= len(alt) <= variant_max_length
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
                    payload.variant_min_length <= len(alt) <= variant_max_length
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
                    payload.variant_min_length <= len(alt) <= variant_max_length
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
                    payload.variant_min_length <= len(alt) <= variant_max_length
                ]
            else:
                # For structural variants that aren't otherwise recognisable
                hit_indexes = [
                    i for i, alt in enumerate(alts)
                    if alt.startswith(v_prefix)
                    and 
                    payload.variant_min_length <= len(alt) <= variant_max_length
                ]
        # if alternate base defined
        # here we should check for the asked variant lengths
        else:
            if payload.alternate_bases == 'N':
                hit_indexes = [
                    i for i, alt in enumerate(alts)
                    if alt.upper() in BASES 
                    and 
                    payload.variant_min_length <= len(alt) <= variant_max_length
                ]
            else:
                hit_indexes = [
                    i for i, alt in enumerate(alts)
                    if alt.upper() == payload.alternate_bases
                    and 
                    payload.variant_min_length <= len(alt) <= variant_max_length
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
            if not payload.include_details:
                break
            hit_string = '|'.join(str(i + 1) for i in hit_indexes)
            pattern = re.compile(f'(^|[|/])({hit_string})([|/]|$)')
            # if payload.requested_granularity in ('record', 'aggregated'):
            #     sample_indices.update([i for i, gt in enumerate(genotypes.split(',')) if pattern.search(gt)])
        
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
        
        # if only bool is asked and a variant if found
        if payload.requested_granularity == 'boolean' and exists:
            break
    query_process.stdout.close()

    # if payload.requested_granularity in ('record', 'aggregated'):
    #     sample_names = [sample for n, sample in enumerate(all_sample_names) if n in sample_indices]
    print('bcftools complete')
    response = PerformQueryResponse(
        exists = exists,
        dataset_id = payload.dataset_id,
        vcf_location =  payload.vcf_location,
        all_alleles_count = all_alleles_count,
        variants = variants,
        call_count = call_count,
        sample_indices = [], #list(sample_indices),
        sample_names = [] #sample_names
    )

    try:
        uuid = uuid4().hex
        body = response.dumps()

        query = db.VariantQuery(payload.query_id)
        result = db.VariantResponse(payload.query_id)
        result.responseNumber = query.getResponseNumber()

        if len(body) < 1024 * 300:
            # response
            result.checkS3 = False
            result.result = body
        else:
            key = f'variant-queries/{uuid}.json'
            s3.put_object(
                Body = body.encode(),
                Bucket = VARIANTS_BUCKET,
                Key = key
            )
            print(f'Uploaded - {VARIANTS_BUCKET}/{key}')
            # s3 details
            s3loc = db.S3Location()
            s3loc.bucket = VARIANTS_BUCKET
            s3loc.key = key
            # response
            result.responseLocation = s3loc
            result.checkS3 = True
        # TODO make more elegant
        errored = True
        msg = ''
        for _ in range(10):
            try:
                result.save()
                errored = False
                break
            except Exception as e:
                print('retrying')
                msg = e
                time.sleep(1)
        if errored:
            print('ERRORED ', msg)
        query.markFinished()
    except ClientError as e:
        print(f"Error: {e}")

    return response
