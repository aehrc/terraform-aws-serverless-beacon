from collections import Counter
import json
import os

import boto3

DATASETS_TABLE_NAME = os.environ['DATASETS_TABLE']
SUMMARISE_VCF_SNS_TOPIC_ARN = os.environ['SUMMARISE_VCF_SNS_TOPIC_ARN']
VCF_SUMMARIES_TABLE_NAME = os.environ['VCF_SUMMARIES_TABLE']

COUNTS = [
    'variantCount',
    'callCount',
    'sampleCount',
]

dynamodb = boto3.resource('dynamodb')
sns = boto3.resource('sns')


def get_locations_info(locations):
    items = []
    num_locations = len(locations)
    offset = 0
    kwargs = {
        'RequestItems': [
            {
                VCF_SUMMARIES_TABLE_NAME: {
                    'ProjectionExpression': ('vcfLocation,updating,'
                                             + ','.join(COUNTS)),
                    'Keys': [],
                },
            },
        ],
    }
    while offset < num_locations:
        to_get = locations[offset:100]
        kwargs['RequestItems'][0][VCF_SUMMARIES_TABLE_NAME]['Keys'] = [
            {'S': loc} for loc in to_get
        ]
        more_results = True
        while more_results:
            print("batch_get_item: {}".format(json.dumps(kwargs)))
            response = dynamodb.batch_get_item(**kwargs)
            print("Received response: {}".format(json.dumps(response)))
            items += response['Responses'][VCF_SUMMARIES_TABLE_NAME]
            if 'UnprocessedKeys' in response:
                kwargs['RequestItems'] = response['UnprocessedKeys']
                more_results = True
    return items


def summarise_dataset(dataset):
    vcf_locations = dataset['vcfLocations']['L']
    locations_info = get_locations_info(vcf_locations)
    new_locations = set(vcf_locations)
    counts = Counter()
    updated = True
    for location in locations_info:
        vcf_location = location['vcfLocation']
        new_locations.remove(vcf_location)
        if 'updating' in location:
            updated = False
        if any(count not in location for count in COUNTS):
            updated = False
            summarise_vcf(vcf_location)
        elif updated:
            counts.update({count: int(location[count]['N'])
                           for count in COUNTS})
    if new_locations:
        updated = False
    for new_location in new_locations:
        summarise_vcf(new_location)
    if updated:
        values = {':'+count: {'N': str(count)} for count in COUNTS}
    else:
        values = {':'+count: {'NULL': True} for count in COUNTS}

    update_dataset(dataset['id']['S'], values)


def summarise_vcf(location):
    kwargs = {
        'TopicArn': SUMMARISE_VCF_SNS_TOPIC_ARN,
        'Message': location,
    }
    print('Publishing to SNS: {}'.format(json.dumps(kwargs)))
    response = sns.publish(**kwargs)
    print('Received Response: {}'.format(json.dumps(response)))


def update_dataset(dataset_id, values):
    kwargs = {
        'TableName': DATASETS_TABLE_NAME,
        'Key': {
            'id': {
                'S': dataset_id,
            },
        },
        'UpdateExpression': 'SET ' + ', '.join('{c}=:{c}'.format(c=count)
                                               for count in COUNTS),
        'ExpressionAttributeValues': values,
    }
    print('Updating item: {}'.format(json.dumps(kwargs)))
    dynamodb.update_item(**kwargs)


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    dataset = json.loads(event[0]['Sns']['Message'])
    summarise_dataset(dataset)
