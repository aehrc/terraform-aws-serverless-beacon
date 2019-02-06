import json
import os
import subprocess

import boto3
from botocore.exceptions import ClientError

from chrom_matching import CHROMOSOME_LENGTHS_MBP, get_vcf_chromosomes, get_matching_chromosome

COUNTS = [
    'variantCount',
    'callCount',
    'sampleCount',
]

SLICE_SIZE_MBP = 20

SUMMARISE_SLICE_SNS_TOPIC_ARN = os.environ['SUMMARISE_SLICE_SNS_TOPIC_ARN']
VCF_SUMMARIES_TABLE_NAME = os.environ['VCF_SUMMARIES_TABLE']

os.environ['PATH'] += ':' + os.environ['LAMBDA_TASK_ROOT']

dynamodb = boto3.client('dynamodb')
sns = boto3.client('sns')

regions = {}
for chrom, size in CHROMOSOME_LENGTHS_MBP.items():
    chrom_regions = []
    start = 0
    while start < size:
        chrom_regions.append(start)
        start += SLICE_SIZE_MBP
    regions[chrom] = chrom_regions


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


def get_translated_regions(location):
    vcf_chromosomes = get_vcf_chromosomes(location)
    vcf_regions = []
    for target_chromosome, region_list in regions.items():
        chromosome = get_matching_chromosome(vcf_chromosomes, target_chromosome)
        if not chromosome:
            continue
        vcf_regions += ['{}:{}'.format(chromosome, region)
                        for region in region_list]
    return vcf_regions


def mark_updating(location, vcf_regions):
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
                'SS': vcf_regions,
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


def publish_slice_updates(location, vcf_regions):
    kwargs = {
        'TopicArn': SUMMARISE_SLICE_SNS_TOPIC_ARN,
    }
    for region in vcf_regions:
        kwargs['Message'] = json.dumps({
            'location': location,
            'region': region,
            'slice_size_mbp': SLICE_SIZE_MBP,
        })
        print('Publishing to SNS: {}'.format(json.dumps(kwargs)))
        response = sns.publish(**kwargs)
        print('Received Response: {}'.format(json.dumps(response)))


def summarise_vcf(location):
    vcf_regions = get_translated_regions(location)
    start_update = mark_updating(location, vcf_regions)
    if not start_update:
        return
    sample_count = get_sample_count(location)
    update_sample_count(location, sample_count)
    publish_slice_updates(location, vcf_regions)


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
