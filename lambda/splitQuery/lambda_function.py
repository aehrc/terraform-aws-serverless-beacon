import json
import os
import queue
import threading
from collections import defaultdict
import boto3
import jsons

from lambda_payloads import SplitQueryPayload, PerformQueryPayload


SPLIT_SIZE = 1000000
PERFORM_QUERY = os.environ['PERFORM_QUERY_LAMBDA']

aws_lambda = boto3.client('lambda')


def perform_query(payload, responses):

    print(f"Invoking {PERFORM_QUERY} with payload: {jsons.dump(payload)}")
    response = aws_lambda.invoke(
        FunctionName=PERFORM_QUERY,
        InvocationType='Event',
        Payload=jsons.dumps(payload),
    )
    # response_json = response['Payload'].read()
    # print(f"vcf_location='{payload.vcf_location}', \
    #         region='{payload.region}': \
    #         received payload: {response_json}")
    # response_dict = json.loads(response_json)
    # # For separating samples by vcf
    # response_dict['vcf_location'] = payload.vcf_location
    # responses.put(response_dict)


def split_query(split_payload: SplitQueryPayload):
    responses = queue.Queue()
    # to find HITs or ALL we must analyse all vcfs
    check_all = split_payload.include_datasets in ('HIT', 'ALL')
    # create an id for each vcf group for identification
    vcf_file_to_group_map = {loc: idx for idx, grp in enumerate(split_payload.vcf_groups) for loc in grp}
    vcf_group_to_file_map = {idx: loc for idx, grp in enumerate(split_payload.vcf_groups) for loc in grp}

    threads = []
    split_start = split_payload.region_start

    while split_start <= split_payload.region_end:
        split_end = min(split_start + SPLIT_SIZE - 1, split_payload.region_end)
        # perform query on this split of the vcf
        for vcf_location, chrom in split_payload.vcf_locations.items():
            # region for bcftools
            payload = PerformQueryPayload(
                dataset_id=split_payload.dataset_id,
                query_id=split_payload.query_id,
                reference_bases=split_payload.reference_bases,
                end_min=split_payload.end_min,
                end_max=split_payload.end_max,
                alternate_bases=split_payload.alternate_bases,
                variant_type=split_payload.variant_type,
                requested_granularity=split_payload.requested_granularity,
                variant_min_length=split_payload.variant_min_length,
                variant_max_length=split_payload.variant_max_length,
                include_details=check_all,
                region=f'{chrom}:{split_start}-{split_end}',
                vcf_location=vcf_location
            )
            t = threading.Thread(
                    target=perform_query, 
                    kwargs={
                        'payload': payload, 
                        'responses': responses
                    }
                )
            t.start()
            threads.append(t)
        # next split
        split_start += SPLIT_SIZE

    for thread in threads:
        thread.join()

    return


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    split_payload = jsons.load(event, SplitQueryPayload)
    response = split_query(split_payload)
    print('Completed split query')

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
