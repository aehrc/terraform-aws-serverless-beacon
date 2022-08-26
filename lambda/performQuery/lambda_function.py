import json
import jsons
import re

import search_variants
import search_variant_samples
from payloads.lambda_payloads import PerformQueryPayload

BASES = [
    'A',
    'C',
    'G',
    'T',
    'N',
]

all_count_pattern = re.compile('[0-9]+')
get_all_calls = all_count_pattern.findall


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    performQueryPayload = jsons.load(event, PerformQueryPayload)
    # switch operations
    if performQueryPayload.passthrough.get('samplesOnly', False):
        response = search_variant_samples.perform_query(performQueryPayload)
    else:
        response = search_variants.perform_query(performQueryPayload)

    print(f'Returning response: \n {response.dump()}')
    return response.dump()


if __name__ == '__main__':
    # # event = {
    # #     "alternate_bases": "G",
    # #     "dataset_id": "pop-2-wic",
    # #     "end_max": 10000659,
    # #     "end_min": 10000658,
    # #     "include_details": True,
    # #     "passthrough": {
    # #         'samplesOnly': True
    # #     },
    # #     "query_id": "ac0163962988414ca28f1d5138867b40",
    # #     "reference_bases": "A",
    # #     "region": "5:10000658-10000659",
    # #     "requested_granularity": "record",
    # #     "variant_max_length": -1,
    # #     "variant_min_length": 0,
    # #     "variant_type": None,
    # #     "vcf_location": "s3://simulationexperiments/test-vcfs/100.chr5.80k.vcf.gz"
    # # }

    # event = {
    #     "alternate_bases": "T",
    #     "dataset_id": "pop-2-wic",
    #     "end_max": 10000320,
    #     "end_min": 10000319,
    #     "include_details": True,
    #     "passthrough": {
    #         "samplesOnly": True
    #     },
    #     "query_id": "32742a29f7bd4cddb47787d66b0f11e9",
    #     "reference_bases": "A",
    #     "region": "5:10000319-10000320",
    #     "requested_granularity": "count",
    #     "variant_max_length": -1,
    #     "variant_min_length": 0,
    #     "variant_type": None,
    #     "vcf_location": "s3://vcf-simulations/population-2-chr5-1000-samples-seed-2-5-full.vcf.gz"
    # }

    event = {
        "alternate_bases": "N",
        "dataset_id": "pop-2-wic",
        "end_max": 10001001,
        "end_min": 10000001,
        "include_details": True,
        "passthrough": {},
        "query_id": "680afc7615fc40818704c4c5af36a498",
        "reference_bases": "A",
        "region": "5:10000001-10001001",
        "requested_granularity": "record",
        "variant_max_length": -1,
        "variant_min_length": 0,
        "variant_type": None,
        "vcf_location": "s3://vcf-simulations/population-2-chr5-1000-samples-seed-2-5-full.vcf.gz"
    }



    lambda_handler(event, dict())