import json
import jsons
import re

import search_variants
import search_variant_samples
import search_variants_in_samples
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
    
    try:
        event = json.loads(event['Records'][0]['Sns']['Message'])
        print('using sns event')
    except:
        print('using invoke event')

    performQueryPayload = jsons.load(event, PerformQueryPayload)
    # switch operations
    if performQueryPayload.passthrough.get('samplesOnly', False):
        response = search_variant_samples.perform_query(performQueryPayload)
    elif performQueryPayload.passthrough.get('selectedSamplesOnly', False):
        response = search_variants_in_samples.perform_query(performQueryPayload)
    else:
        response = search_variants.perform_query(performQueryPayload)

    print(f'Returning response')
    return response.dump()


if __name__ == '__main__':
    pass
