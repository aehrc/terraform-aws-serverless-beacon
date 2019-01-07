import json
import os
import subprocess

import boto3
from botocore.exceptions import ClientError

COUNTS = [
    'variantCount',
    'callCount',
    'sampleCount',
]

CHROMOSOME_LENGTHS = {
    '1': 248956422,
    '2': 242193529,
    '3': 198295559,
    '4': 190214555,
    '5': 181538259,
    '6': 170805979,
    '7': 159345973,
    '8': 145138636,
    '9': 138394717,
    '10': 133797422,
    '11': 135086622,
    '12': 133275309,
    '13': 114364328,
    '14': 107043718,
    '15': 101991189,
    '16': 90338345,
    '17': 83257441,
    '18': 80373285,
    '19': 58617616,
    '20': 64444167,
    '21': 46709983,
    '22': 50818468,
    'X': 156040895,
    'Y': 57227415,
    'MT': 16569,
}

SLICE_SIZE = 2000000

SUMMARISE_SLICE_SNS_TOPIC_ARN = os.environ('SUMMARISE_SLICE_SNS_TOPIC_ARN')
VCF_SUMMARIES_TABLE_NAME = os.environ['VCF_SUMMARIES_TABLE']

dynamodb = boto3.client('dynamodb')
sns = boto3.client('sns')

regions = []
for chrom, size in CHROMOSOME_LENGTHS.items():
    start = 1
    while start <= size:
        end = start + SLICE_SIZE - 1
        regions.append('{c}:{s}-{e}'.format(c=chrom, s=start, e=end))
        start = end + 1


def get_sample_count(location):
    args = [
        'bcftools', 'view',
        '--header-only',
        '--no-version',
        location
    ]
    header = subprocess.check_output(args, cwd='/tmp')
    # Get the number of tabs after the INFO column in the last header line
    return header.count('\t', header.find('INFO', header.rfind('\n')))


def mark_updating(location):
    kwargs = {
        'TableName': VCF_SUMMARIES_TABLE_NAME,
        'Key': {
            'vcfLocation': {
                'S': location,
            },
        },
        'UpdateExpression': 'SET toUpdate=:toUpdate, updating=:updating'
                            ' REMOVE ' + ', '.join(COUNTS),
        'ExpressionAttributeValues': {
            ':toUpdate': {
                'SS': regions,
            },
            ':updating': {
                'BOOL': True,
            },
        },
        'ConditionExpression': 'attribute_not_exists(updating)',
    }
    print('Updating table: {}'.format(json.dumps(kwargs)))
    try:
        dynamodb.update_item(**kwargs)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            print("VCF location is already updating, aborting.")
            return False
        else:
            raise e
    return True


def publish_slice_updates(location):
    kwargs = {
        'TopicArn': SUMMARISE_SLICE_SNS_TOPIC_ARN,
    }
    for region in regions:
        kwargs['Message'] = json.dumps({
            'location': location,
            'region': region,
        })
        print('Publishing to SNS: {}'.format(json.dumps(kwargs)))
        response = sns.publish(**kwargs)
        print('Received Response: {}'.format(json.dumps(response)))


def summarise_vcf(location):
    start_update = mark_updating(location)
    if not start_update:
        return
    sample_count = get_sample_count(location)
    update_sample_count(location, sample_count)
    publish_slice_updates(location)


def update_sample_count(location, sample_count):
    kwargs = {
        'TableName': VCF_SUMMARIES_TABLE_NAME,
        'Key': {
            'VcfLocation': {
                'S': location,
            },
        },
        'UpdateExpression': 'SET sampleCount=:sampleCount',
        'ExpressionAttributeValues': {
            ':sampleCount': {
                'N': str(sample_count),
            },
        },
    }
    print('Updating table: {}'.format(json.dumps(kwargs)))
    dynamodb.update_item(**kwargs)


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    location = event[0]['Sns']['Message']
    summarise_vcf(location)
