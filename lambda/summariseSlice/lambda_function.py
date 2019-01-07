import json
import os
import subprocess

import boto3
from botocore.exceptions import ClientError

ASSEMBLY_GSI = os.environ['ASSEMBLY_GSI']
DATASETS_TABLE_NAME = os.environ['DATASETS_TABLE']
SUMMARISE_DATASET_SNS_TOPIC_ARN = os.environ['SUMMARISE_DATASET_SNS_TOPIC_ARN']
VCF_SUMMARIES_TABLE_NAME = os.environ['VCF_SUMMARIES_TABLE']


dynamodb = boto3.client('dynamodb')
sns = boto3.client('sns')


def get_affected_datasets(location):
    kwargs={
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


def get_counts_handle(location, region):
    args = [
        'bcftools', 'query',
        '--regions', region,
        '--format', '%INFO/AN\t%INFO/AC\n',
        location
    ]
    query_process = subprocess.Popen(args, stdout=subprocess.PIPE, cwd='/tmp')
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
        return True
    else:
        return False


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
    for record in counts_handle:
        call_num_str, alt_allele_num_str = record.strip('\r\n').split('\t')
        # Add the AN value to the call count
        call_count += int(call_num_str)
        # Add the total number of alt alleles with nonzero counts to variant
        # count
        variant_count += sum(1 for alt in alt_allele_num_str.split(',')
                             if int(alt))
    return call_count, variant_count


def summarise_slice(location, region):
    counts_handle = get_counts_handle(location, region)
    call_count, variant_count = sum_counts(counts_handle)
    counts_handle.close()
    update_complete = update_vcf(location, region, variant_count, call_count)
    if update_complete:
        impacted_datasets = get_affected_datasets(location)
        summarise_datasets(impacted_datasets)


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    message = json.loads(event[0]['Sns']['Message'])
    location = message['location']
    region = message['region']
    summarise_slice(location, region)
