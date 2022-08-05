import json
import jsons
import re
import subprocess

import search_variants
import search_variant
from lambda_payloads import PerformQueryPayload

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
    response = search_variants.perform_query(performQueryPayload)
    print(f'Returning response: \n {response.dump()}')
    return response.dump()


if __name__ == '__main__':
    event = {
        "region": "5:10000001-10001001",
        "reference_bases": "A",
        "end_min": 10000001,
        "end_max": 10001001,
        "alternate_bases": "G",
        "variant_type": None,
        "include_details": True,
        "dataset_id": 'test',
        'requested_granularity': 'record',
        'variant_min_length': 0,
        'variant_max_length': -1,
        "vcf_location": "s3://simulationexperiments/test-vcfs/100.chr5.80k.vcf.gz"
    }

    lambda_handler(event, dict())