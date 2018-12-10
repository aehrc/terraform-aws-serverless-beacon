import json
import os
import re
import subprocess

os.environ['PATH'] += ':' + os.environ['LAMBDA_TASK_ROOT']


def perform_query(dataset_id, vcf_location, start, reference_name,
                  reference_bases, alternate_bases, include_datasets):
    args = [
        'bcftools', 'query',
        '--regions', '{}:{}'.format(reference_name, start+1),
        '--format', '%REF\t%ALT\t%INFO/AC\t%INFO/AN\t[,%GT,]',
        vcf_location
    ]
    query_process = subprocess.Popen(args, stdout=subprocess.PIPE, cwd='/tmp',
                                     encoding='ascii')
    response = {
        'datasetId': dataset_id,
        'include': False,
        'exists': None,
        'error': None,
        'frequency': None,
        'variantCount': None,
        'callCount': None,
        'sampleCount': None,
        'note': None,
        'externalUrl': None,
        'info': None,
    }
    exists = False
    for line in query_process.stdout:
        first_delim = line.find('\t')
        if line[:first_delim] == reference_bases:
            second_delim = line.find('\t', first_delim+1)
            alts = line[first_delim+1:second_delim].split(',')
            alt_index = alts.index(alternate_bases)
            if alt_index >= 0:
                third_delim = line.find('\t', second_delim+1)
                alt_call_counts = line[second_delim+1:third_delim].split(',')
                call_count = int(alt_call_counts[alt_index])
                if call_count > 0:
                    exists = True
                    if include_datasets in ('HIT', 'ALL'):
                        fourth_delim = line.find('\t', third_delim+1)
                        allele_number = int(line[third_delim+1:fourth_delim])
                        frequency = 1.0 * call_count / allele_number
                        alt_number = alt_index + 1
                        sample_count = len(re.findall(
                            ',([0-9.]+[|/])*{}[|/,]'.format(alt_number),
                            line[fourth_delim+1:]
                        ))
                        response.update({
                            'include': True,
                            'frequency': frequency,
                            'variantCount': 1,
                            'sampleCount': sample_count,
                            'callCount': call_count,
                        })
                break
    query_process.stdout.close()
    if exists:
        response['exists'] = True
    else:
        response['exists'] = False
        if include_datasets in ('MISS', 'ALL'):
            response.update({
                'include': True,
                'frequency': 0,
                'variantCount': 0,
                'sampleCount': 0,
                'callCount': 0,
            })
    return response


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    vcf_location = event['vcf_location']
    start = event['start']
    dataset_id = event['dataset_id']
    reference_name = event['reference_name']
    reference_bases = event['reference_bases']
    alternate_bases = event['alternate_bases']
    include_datasets = event['include_datasets']
    response = perform_query(
        dataset_id, vcf_location, start, reference_name, reference_bases,
        alternate_bases, include_datasets
    )
    print('Returning response: {}'.format(json.dumps(response)))
    return response


