import os
import jsons
import re
import subprocess
from uuid import uuid4
import boto3
from botocore.exceptions import ClientError

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
        payload.vcf_location
    ]
    query_process = subprocess.Popen(args, stdout=subprocess.PIPE, cwd='/tmp', encoding='ascii')
    # region is of form: "chrom:start-end"
    first_bp = int(payload.region[payload.region.find(':') + 1: payload.region.find('-')])
    sample_indices = set()
    sample_names = []
    count = 0
    all_alleles_count = 0

    # iterate through bcftools output
    for line in query_process.stdout:
        try:
            (position, reference, all_alts, info_str, genotypes) = line.strip().split('\t')
        except ValueError as e:
            print(repr(line.split('\t')))
            raise e

        pos = int(position)
        alts = all_alts.split(',')

        if pos != first_bp or payload.reference_bases != reference or payload.alternate_bases not in alts:
            continue
        
        try:
            alt_index = alts.index(payload.alternate_bases) + 1
            genotypes = genotypes.strip(',').split(',')

            for index, genotype in enumerate(genotypes):
                if genotype == '.':
                    continue
                genotype = get_all_calls(genotype)
                all_alleles_count += len(genotype)

                if alt_index in { int(allele) for allele in genotype }:
                    sample_indices.add(index) 
        except Exception as e:
            print('Errored', e)

    query_process.stdout.close()

    if payload.requested_granularity in ('record', 'aggregated'):
        args = [
            'bcftools', 'query',
            '--list-samples',
            payload.vcf_location
        ]
        samples_process = subprocess.Popen(args, stdout=subprocess.PIPE, cwd='/tmp', encoding='ascii')
        sample_names = [line.strip() for n, line in enumerate(samples_process.stdout) if n in sample_indices]
        samples_process.stdout.close()
        count = len(sample_indices)

    if payload.requested_granularity == 'count':
        count = len(sample_indices)

    response = PerformQueryResponse(
        exists = len(sample_indices) > 0,
        dataset_id = payload.dataset_id,
        vcf_location =  payload.vcf_location,
        variants = [],
        call_count = count,
        sample_indices = [],
        sample_names = list(sample_names),
        all_alleles_count=all_alleles_count
    )

    try:
        uuid = uuid4().hex
        key = f'variant-queries/{uuid}.json'
        s3.put_object(
            Body = response.dumps().encode(),
            Bucket = VARIANTS_BUCKET,
            Key = key
        )

        print(f'Uploaded - {VARIANTS_BUCKET}/{key}')
        query = db.VariantQuery(payload.query_id)
        result = db.VariantResponse(payload.query_id)
        result.responseNumber = query.getResponseNumber()
        s3loc = db.S3Location()
        s3loc.bucket = VARIANTS_BUCKET
        s3loc.key = key
        result.responseLocation = s3loc
        result.save()
        query.markFinished()
    except ClientError as e:
        print(f"Error: {e}")

    return response
