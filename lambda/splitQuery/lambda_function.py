import json
import os
import queue
import threading
from collections import defaultdict
import boto3
import jsons

import lambda_payloads as payloads


SPLIT_SIZE = 1000000
PERFORM_QUERY = os.environ['PERFORM_QUERY_LAMBDA']

aws_lambda = boto3.client('lambda')


def perform_query(
        region, 
        reference_bases, 
        end_min, 
        end_max, 
        alternate_bases,
        variant_type, 
        include_details, 
        requested_granularity, 
        vcf_location, 
        variant_min_length,
        variant_max_length, 
        responses):

    payload = json.dumps({
        'region': region,
        'reference_bases': reference_bases,
        'end_min': end_min,
        'end_max': end_max,
        'alternate_bases': alternate_bases,
        'variant_type': variant_type,
        'include_details': include_details,
        'vcf_location': vcf_location,
        'variant_min_length': variant_min_length,
        'variant_max_length': variant_max_length,
        'requested_granularity': requested_granularity
    })
    print(f"Invoking {PERFORM_QUERY} with payload: {payload}")
    response = aws_lambda.invoke(
        FunctionName=PERFORM_QUERY,
        Payload=payload,
    )
    response_json = response['Payload'].read()
    print(f"vcf_location='{vcf_location}', region='{region}': received payload: {response_json}")
    response_dict = json.loads(response_json)
    # For separating samples by vcf
    response_dict['vcf_location'] = vcf_location
    responses.put(response_dict)


def split_query(splitQueryPayload):
    responses = queue.Queue()
    # to find HITs or ALL we must analyse all vcfs
    check_all = splitQueryPayload.include_datasets in ('HIT', 'ALL')
    # create an id for each vcf group for identification
    vcf_file_to_group_map = {loc: idx for idx, grp in enumerate(splitQueryPayload.vcf_groups) for loc in grp}
    vcf_group_to_file_map = {idx: loc for idx, grp in enumerate(splitQueryPayload.vcf_groups) for loc in grp}

    kwargs = {
        'reference_bases': splitQueryPayload.reference_bases,
        'end_min': splitQueryPayload.end_min,
        'end_max': splitQueryPayload.end_max,
        'alternate_bases': splitQueryPayload.alternate_bases,
        'variant_type': splitQueryPayload.variant_type,
        'requested_granularity': splitQueryPayload.requested_granularity,
        'variant_min_length': splitQueryPayload.variant_min_length,
        'variant_max_length': splitQueryPayload.variant_max_length,
        # Don't bother recording details from MISS, they'll all be 0s
        'include_details': check_all,
        'responses': responses,
    }
    threads = []
    split_start = splitQueryPayload.region_start

    while split_start <= splitQueryPayload.region_end:
        split_end = min(split_start + SPLIT_SIZE - 1, splitQueryPayload.region_end)
        # perform query on this split of the vcf
        for vcf_location, chrom in splitQueryPayload.vcf_locations.items():
            # region for bcftools
            kwargs['region'] = '{}:{}-{}'.format(chrom, split_start,
                                                 split_end)
            # vcf file in s3
            kwargs['vcf_location'] = vcf_location
            t = threading.Thread(target=perform_query, kwargs=kwargs)
            t.start()
            threads.append(t)
        split_start += SPLIT_SIZE

    num_threads = len(threads)
    processed = 0
    all_alleles_count = 0
    variants = set()
    variants_vcf_map = defaultdict(set)
    call_count = 0
    vcf_samples = defaultdict(set)
    vcf_sample_names = defaultdict(set)
    exists = False

    while processed < num_threads and (check_all or not exists):
        response = responses.get()
        processed += 1
        if 'exists' not in response:
            # function errored out, ignore
            continue
        # variants exists in split
        exists_in_split = response['exists']

        if exists_in_split:
            exists = True
            if check_all:
                all_alleles_count += response['all_alleles_count']
                variants.update(response['variants'])
                call_count += response['call_count']
                vcf_location = response['vcf_location']
                for variant in response['variants']:
                    variants_vcf_map[variant].add(vcf_location)
                sample_indices = response['sample_indices']
                sample_names = response['sample_names']
                # separate unrelated samples into dintinct groups as per indicated by
                vcf_group = vcf_file_to_group_map[vcf_location]

                # for each sample group record the response
                # a sample can have only one hit in one file (i.e., no duplicate variants)
                # but different sample groups can have variants in different files (if submitted like that) 
                vcf_samples[vcf_group].update(sample_indices)
                vcf_sample_names[vcf_group].update(sample_names)

    if (splitQueryPayload.include_datasets == 'ALL' or (splitQueryPayload.include_datasets == 'HIT' and exists)
        # if we want all datasets or HITs given we have hits
        or 
        # if we want to include MISS and variants found found
        (splitQueryPayload.include_datasets == 'MISS' and not exists)):
        response_dict = {
            'datasetId': splitQueryPayload.dataset_id,
            'exists': exists,
            'frequency': ((all_alleles_count or call_count and None)
                          and call_count / all_alleles_count),
            'variantCount': len(variants),
            'callCount': call_count,
            'sampleCount': sum(len(samples)
                               for samples in vcf_samples.values()),
            'note': None,
            'externalUrl': None,
            'info': None,
            'error': None,
        }

        if splitQueryPayload.requested_granularity in ('record', 'aggregated'):
            response_dict['samples'] = list(set(s for sn in vcf_sample_names.values() for s in sn))
            variants_vcf_map = {k: list(v) for k, v in variants_vcf_map.items()}
            response_dict['variants'] = variants_vcf_map
    else:
        response_dict = {
            'include': False,
            'exists': exists,
        }
    return response_dict


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    splitQueryPayload = jsons.load(event, payloads.SplitQueryPayload)
    response = split_query(splitQueryPayload)
    print('Returning response: {}'.format(json.dumps(response)))

    return response


if __name__ == '__main__':
    event = {
        "dataset_id": "test-wic",
        "reference_bases": "A",
        "region_start": 10000001,
        "region_end": 10001001,
        "end_min": 10000001,
        "end_max": 10001001,
        "alternate_bases": "N",
        "variant_type": None,
        "include_datasets": "HIT",
        "vcf_locations": {
            "s3://simulationexperiments/test-vcfs/100.chr5.80k.vcf.gz": "5"
        },
        "vcf_groups": [
            [
                "s3://simulationexperiments/test-vcfs/100.chr5.80k.vcf.gz"
            ]
        ],
        "requested_granularity": "record",
        "variant_min_length": 0,
        "variant_max_length": -1
    }

    lambda_handler(event, dict())
