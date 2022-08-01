import json
import os
import queue
import threading
from collections import defaultdict

import boto3


SPLIT_SIZE = 1000000
PERFORM_QUERY = os.environ['PERFORM_QUERY_LAMBDA']

aws_lambda = boto3.client('lambda')


def perform_query(region, reference_bases, end_min, end_max, alternate_bases,
                  variant_type, include_details, requested_granularity, vcf_location, responses):
    payload = json.dumps({
        'region': region,
        'reference_bases': reference_bases,
        'end_min': end_min,
        'end_max': end_max,
        'alternate_bases': alternate_bases,
        'variant_type': variant_type,
        'include_details': include_details,
        'vcf_location': vcf_location,
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


def split_query(dataset_id, reference_bases, region_start,
                region_end, end_min, end_max, alternate_bases, variant_type,
                include_datasets, vcf_locations, vcf_groups, requested_granularity):
    responses = queue.Queue()
    # to find HITs or ALL we must analyse all vcfs
    check_all = include_datasets in ('HIT', 'ALL')
    # create an id for each vcf group for identification
    vcf_file_to_group_map = {loc: idx for idx, grp in enumerate(vcf_groups) for loc in grp}

    kwargs = {
        'reference_bases': reference_bases,
        'end_min': end_min,
        'end_max': end_max,
        'alternate_bases': alternate_bases,
        'variant_type': variant_type,
        'requested_granularity': requested_granularity,
        # Don't bother recording details from MISS, they'll all be 0s
        'include_details': check_all,
        'responses': responses,
    }
    threads = []
    split_start = region_start

    while split_start <= region_end:
        split_end = min(split_start + SPLIT_SIZE - 1, region_end)
        # perform query on this split of the vcf
        for vcf_location, chrom in vcf_locations.items():
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
                sample_indices = response['sample_indices']
                sample_names = response['sample_names']
                # separate unrelated samples into dintinct groups as per indicated by
                vcf_group = vcf_file_to_group_map[vcf_location]

                # for each sample group record the response
                # a sample can have only one hit in one file (i.e., no duplicate variants)
                # but different sample groups can have variants in different files (if submitted like that) 
                vcf_samples[vcf_group].update(sample_indices)
                vcf_sample_names[vcf_group].update(sample_names)

    if (include_datasets == 'ALL' or (include_datasets == 'HIT' and exists)
        # if we want all datasets or HITs given we have hits
        or 
        # if we want to include MISS and variants found found
        (include_datasets == 'MISS' and not exists)):
        response_dict = {
            'datasetId': dataset_id,
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

        if requested_granularity in ('record', 'aggregated'):
            response_dict['samples'] = list(set(s for sn in vcf_sample_names.values() for s in sn))
            response_dict['variants'] = list(variants)
    else:
        response_dict = {
            'include': False,
            'exists': exists,
        }
    return response_dict


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))

    dataset_id = event['dataset_id']
    reference_bases = event['reference_bases']
    region_start = event['region_start']
    region_end = event['region_end']
    end_min = event['end_min']
    end_max = event['end_max']
    alternate_bases = event['alternate_bases']
    variant_type = event['variant_type']
    include_datasets = event['include_datasets']
    vcf_locations = event['vcf_locations']
    vcf_groups = event['vcf_groups']
    requested_granularity = event['requested_granularity']

    response = split_query(
        dataset_id=dataset_id,
        reference_bases=reference_bases,
        region_start=region_start,
        region_end=region_end,
        end_min=end_min,
        end_max=end_max,
        alternate_bases=alternate_bases,
        variant_type=variant_type,
        include_datasets=include_datasets,
        vcf_locations=vcf_locations,
        vcf_groups=vcf_groups,
        requested_granularity=requested_granularity
    )
    print(response)
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
        "requested_granularity": "record"
    }

    lambda_handler(event, dict())
