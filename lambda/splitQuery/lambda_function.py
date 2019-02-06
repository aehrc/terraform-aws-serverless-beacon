import json
import os
import queue
import threading

import boto3


SPLIT_SIZE = 1000000
PERFORM_QUERY = os.environ['PERFORM_QUERY_LAMBDA']

aws_lambda = boto3.client('lambda')


def perform_query(region, reference_bases, end_min, end_max, alternate_bases,
                  variant_type, include_details, vcf_location, responses):
    payload = json.dumps({
        'region': region,
        'reference_bases': reference_bases,
        'end_min': end_min,
        'end_max': end_max,
        'alternate_bases': alternate_bases,
        'variant_type': variant_type,
        'include_details': include_details,
        'vcf_location': vcf_location,
    })
    print("Invoking {lambda_name} with payload: {payload}".format(
        lambda_name=PERFORM_QUERY, payload=payload))
    response = aws_lambda.invoke(
        FunctionName=PERFORM_QUERY,
        Payload=payload,
    )
    response_json = response['Payload'].read()
    print("vcf_location='{vcf}', region='{region}':"
          " received payload: {payload}".format(
              vcf=vcf_location, region=region, payload=response_json))
    response_dict = json.loads(response_json)
    # For separating samples by vcf
    response_dict['vcf_location'] = vcf_location
    responses.put(response_dict)


def split_query(dataset_id, reference_bases, region_start,
                region_end, end_min, end_max, alternate_bases, variant_type,
                include_datasets, vcf_locations):
    responses = queue.Queue()
    check_all = include_datasets in ('HIT', 'ALL')
    kwargs = {
        'reference_bases': reference_bases,
        'end_min': end_min,
        'end_max': end_max,
        'alternate_bases': alternate_bases,
        'variant_type': variant_type,
        # Don't bother recording details from MISS, they'll all be 0s
        'include_details': check_all,
        'responses': responses,
    }
    threads = []
    split_start = region_start
    while split_start <= region_end:
        split_end = min(split_start + SPLIT_SIZE - 1, region_end)
        for vcf_location, chrom in vcf_locations.items():
            kwargs['region'] = '{}:{}-{}'.format(chrom, split_start,
                                                 split_end)
            kwargs['vcf_location'] = vcf_location
            t = threading.Thread(target=perform_query,
                                 kwargs=kwargs)
            t.start()
            threads.append(t)
        split_start += SPLIT_SIZE

    num_threads = len(threads)
    processed = 0
    all_alleles_count = 0
    variants = set()
    call_count = 0
    vcf_samples = {}
    exists = False
    while processed < num_threads and (check_all or not exists):
        response = responses.get()
        processed += 1
        if 'exists' not in response:
            # function errored out, ignore
            continue
        exists_in_split = response['exists']
        if exists_in_split:
            exists = True
            if check_all:
                all_alleles_count += response['all_alleles_count']
                variants.update(response['variants'])
                call_count += response['call_count']
                vcf_location = response['vcf_location']
                if vcf_location in vcf_samples:
                    vcf_samples[vcf_location].update(response['samples'])
                else:
                    vcf_samples[vcf_location] = set(response['samples'])
    if (include_datasets == 'ALL' or (include_datasets == 'HIT' and exists)
            or (include_datasets == 'MISS' and not exists)):
        response_dict = {
            'include': True,
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
    )
    print('Returning response: {}'.format(json.dumps(response)))
    return response
