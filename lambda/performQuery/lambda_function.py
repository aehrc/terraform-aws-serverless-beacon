import json
import os
import re
import subprocess

import search_variants
import search_variant

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
    mode = event.get('mode', 'search')

    if mode == 'search':
        print('Running in search mode')
        reference_bases = event['reference_bases']
        region = event['region']
        end_min = event['end_min']
        end_max = event['end_max']
        alternate_bases = event['alternate_bases']
        variant_type = event['variant_type']
        include_details = event['include_details']
        vcf_location = event['vcf_location']
        requested_granularity = event['requested_granularity']
        variant_min_length = event['variant_min_length']
        variant_max_length = event['variant_max_length']

        response = search_variants.perform_query(reference_bases, region, end_min, end_max,
                                alternate_bases, variant_type, include_details,
                                vcf_location, variant_min_length, variant_max_length, requested_granularity)
        print(f'Returning response: \n {json.dumps(response)}')
        return response

    if mode == 'unique':
        position = event['position']
        chrom = event['chrom']
        refbase = event['refbase']
        altbase = event['altbase']
        vcf_location = event['vcf_location']
        requested_granularity = event['requested_granularity']

        response = search_variant.perform_query( 
            chrom,
            position, 
            refbase,
            altbase,
            vcf_location,
            requested_granularity)
        print(f'Returning response: \n {json.dumps(response)}')
        return response


if __name__ == '__main__':
    # event = {
    #     "region": "5:10000001-10001001",
    #     "reference_bases": "A",
    #     "end_min": 10000001,
    #     "end_max": 10001001,
    #     "alternate_bases": "G",
    #     "variant_type": None,
    #     "include_details": True,
    #     'requested_granularity': 'record',
    #     'variant_min_length': 0,
    #     'variant_max_length': -1,
    #     "vcf_location": "s3://simulationexperiments/test-vcfs/100.chr5.80k.vcf.gz"
    # }

    event = {
        "mode": "unique",
        "position": 10000658,
        "chrom": "5",
        "refbase": "A",
        "altbase": "G",
        "vcf_location": "s3://simulationexperiments/test-vcfs/100.chr5.80k.vcf.gz",
        "requested_granularity": "boolean"
    }

    lambda_handler(event, dict())