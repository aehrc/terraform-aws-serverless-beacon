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

CHROMOSOME_LENGTHS_MBP = {
    '1': 248.956422,
    '2': 242.193529,
    '3': 198.295559,
    '4': 190.214555,
    '5': 181.538259,
    '6': 170.805979,
    '7': 159.345973,
    '8': 145.138636,
    '9': 138.394717,
    '10': 133.797422,
    '11': 135.086622,
    '12': 133.275309,
    '13': 114.364328,
    '14': 107.043718,
    '15': 101.991189,
    '16': 90.338345,
    '17': 83.257441,
    '18': 80.373285,
    '19': 58.617616,
    '20': 64.444167,
    '21': 46.709983,
    '22': 50.818468,
    'X': 156.040895,
    'Y': 57.227415,
    'MT': 0.016569,
}

SLICE_SIZE_MBP = 20

SUMMARISE_SLICE_SNS_TOPIC_ARN = os.environ['SUMMARISE_SLICE_SNS_TOPIC_ARN']
VCF_SUMMARIES_TABLE_NAME = os.environ['VCF_SUMMARIES_TABLE']

os.environ['PATH'] += ':' + os.environ['LAMBDA_TASK_ROOT']

dynamodb = boto3.client('dynamodb')
sns = boto3.client('sns')

regions = []
for chrom, size in CHROMOSOME_LENGTHS_MBP.items():
    start = 0
    while start < size:
        regions.append('{c}:{s}'.format(c=chrom, s=start))
        start += SLICE_SIZE_MBP


def get_sample_count(location):
    args = [
        'bcftools', 'view',
        '--header-only',
        '--no-version',
        location
    ]
    header = subprocess.Popen(args, stdout=subprocess.PIPE, cwd='/tmp',
                              encoding='ascii')
    for line in header.stdout:
        if line.startswith('#CHROM'):
            header.stdout.close()
            # Get the number of tabs after the FORMAT column
            return max(line.count('\t') - 8, 0)
    # No header row, probably a bad file.
    raise ValueError("Incorrectly formatted file")


def mark_updating(location):
    kwargs = {
        'TableName': VCF_SUMMARIES_TABLE_NAME,
        'Key': {
            'vcfLocation': {
                'S': location,
            },
        },
        'UpdateExpression': 'SET toUpdate=:toUpdate'
                            ' REMOVE ' + ', '.join(COUNTS),
        'ExpressionAttributeValues': {
            ':toUpdate': {
                'SS': regions,
            },
        },
        'ConditionExpression': 'attribute_not_exists(toUpdate)',
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
            'slice_size_mbp': SLICE_SIZE_MBP,
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
            'vcfLocation': {
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
    location = event['Records'][0]['Sns']['Message']
    summarise_vcf(location)
