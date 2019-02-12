import json
import os
import re
import subprocess

import boto3
from botocore.exceptions import ClientError

ASSEMBLY_GSI = os.environ['ASSEMBLY_GSI']
DATASETS_TABLE_NAME = os.environ['DATASETS_TABLE']
SUMMARISE_DATASET_SNS_TOPIC_ARN = os.environ['SUMMARISE_DATASET_SNS_TOPIC_ARN']
VCF_SUMMARIES_TABLE_NAME = os.environ['VCF_SUMMARIES_TABLE']

os.environ['PATH'] += ':' + os.environ['LAMBDA_TASK_ROOT']

dynamodb = boto3.client('dynamodb')
sns = boto3.client('sns')

all_count_pattern = re.compile('[0-9]+')
get_all_calls = all_count_pattern.findall


def get_affected_datasets(location):
    kwargs = {
        'TableName': DATASETS_TABLE_NAME,
        'IndexName': ASSEMBLY_GSI,
        'ProjectionExpression': 'id',
        'FilterExpression': 'contains(vcfLocations, :location)',
        'ExpressionAttributeValues': {
            ':location': {
                'S': location,
            },
        },
    }
    dataset_ids = []
    still_to_scan = True
    while still_to_scan:
        print("Scanning table: {}".format(json.dumps(kwargs)))
        response = dynamodb.scan(**kwargs)
        print("Received response: {}".format(json.dumps(response)))
        dataset_ids += [item['id']['S'] for item in response.get('Items', [])]
        last_evaluated_key = response.get('LastEvaluatedKey')
        if last_evaluated_key:
            kwargs['ExclusiveStartKey'] = last_evaluated_key
        else:
            still_to_scan = False
    return dataset_ids


def get_counts_handle(location, region_code, slice_size_mbp):
    chrom, start = region_code.split(':')
    args = [
        'bcftools', 'query',
        '--regions', '{chrom}:{start}000001-{end}000000'.format(
            chrom=chrom, start=start, end=int(start)+slice_size_mbp),
        '--format', '[%GT,]\n',
        location
    ]
    query_process = subprocess.Popen(args, stdout=subprocess.PIPE, cwd='/tmp',
                                     encoding='ascii')
    return query_process.stdout


def update_vcf(location, region, variant_count, call_count):
    kwargs = {
        'TableName': VCF_SUMMARIES_TABLE_NAME,
        'Key': {
            'vcfLocation': {
                'S': location,
            },
        },
        'UpdateExpression': 'ADD variantCount :variantCount,'
                            '    callCount :callCount'
                            ' DELETE toUpdate :regionSet',
        'ExpressionAttributeValues': {
            ':variantCount': {
                'N': str(variant_count),
            },
            ':callCount': {
                'N': str(call_count),
            },
            ':regionSet': {
                'SS': [
                    region,
                ],
            },
            ':region': {
                'S': region,
            },
        },
        'ConditionExpression': 'contains(toUpdate, :region)',
        'ReturnValues': 'UPDATED_NEW',
    }
    print('Updating table: {}'.format(json.dumps(kwargs)))
    try:
        response = dynamodb.update_item(**kwargs)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            print("VCF region has already been recorded, aborting.")
            return False
        else:
            raise e
    if response['Attributes'].get('toUpdate'):
        return False
    else:
        return True


def summarise_datasets(datasets):
    kwargs = {
        'TopicArn': SUMMARISE_DATASET_SNS_TOPIC_ARN,
    }
    for dataset in datasets:
        kwargs['Message'] = dataset
        print('Publishing to SNS: {}'.format(json.dumps(kwargs)))
        response = sns.publish(**kwargs)
        print('Received Response: {}'.format(json.dumps(response)))


def sum_counts(counts_handle):
    call_count = 0
    variant_count = 0
    for genotype_str in counts_handle:
            # As AN is often not present, simply manually count all the calls
            calls = get_all_calls(genotype_str)
            call_count += len(calls)
            # Add number of unique non-reference calls to variant count
            call_set = set(calls)
            variant_count += len(call_set) - (1 if '0' in call_set else 0)
    return call_count, variant_count


def summarise_slice(location, region, slice_size_mbp):
    counts_handle = get_counts_handle(location, region, slice_size_mbp)
    call_count, variant_count = sum_counts(counts_handle)
    counts_handle.close()
    update_complete = update_vcf(location, region, variant_count, call_count)
    if update_complete:
        print('Final slice summarised.')
        impacted_datasets = get_affected_datasets(location)
        summarise_datasets(impacted_datasets)


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    message = json.loads(event['Records'][0]['Sns']['Message'])
    location = message['location']
    region = message['region']
    slice_size_mbp = message['slice_size_mbp']
    summarise_slice(location, region, slice_size_mbp)
