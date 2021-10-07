from collections import Counter
from initDuplicateVariantSearch import initDuplicateVariantSearch
import json
import os
import boto3


DATASETS_TABLE_NAME = os.environ['DATASETS_TABLE']
SUMMARISE_VCF_SNS_TOPIC_ARN = os.environ['SUMMARISE_VCF_SNS_TOPIC_ARN']
VCF_SUMMARIES_TABLE_NAME = os.environ['VCF_SUMMARIES_TABLE']

BATCH_GET_MAX_ITEMS = 100

COUNTS = [
    'callCount',
    'sampleCount',
]

dynamodb = boto3.client('dynamodb')
sns = boto3.client('sns')


def get_locations(dataset):
    kwargs = {
        'TableName': DATASETS_TABLE_NAME,
        'ProjectionExpression': 'vcfLocations',
        'ConsistentRead': True,
        'KeyConditionExpression': 'id = :id',
        'ExpressionAttributeValues': {
            ':id': {
                'S': dataset,
            },
        },
    }
    print("Querying table: {}".format(json.dumps(kwargs)))
    response = dynamodb.query(**kwargs)
    print("Received response: {}".format(json.dumps(response)))
    return response['Items'][0].get('vcfLocations', {}).get('SS', [])


def get_locations_info(locations):
    items = []
    num_locations = len(locations)
    offset = 0
    kwargs = {
        'RequestItems': {
            VCF_SUMMARIES_TABLE_NAME: {
                'ProjectionExpression': ('vcfLocation,toUpdate,'
                                         + ','.join(COUNTS)),
                'Keys': [],
            },
        },
    }
    while offset < num_locations:
        to_get = locations[offset:offset+BATCH_GET_MAX_ITEMS]
        kwargs['RequestItems'][VCF_SUMMARIES_TABLE_NAME]['Keys'] = [
            {
                'vcfLocation': {
                    'S': loc,
                },
            } for loc in to_get
        ]
        more_results = True
        while more_results:
            print("batch_get_item: {}".format(json.dumps(kwargs)))
            response = dynamodb.batch_get_item(**kwargs)
            print("Received response: {}".format(json.dumps(response)))
            items += response['Responses'][VCF_SUMMARIES_TABLE_NAME]
            unprocessed_keys = response.get('UnprocessedKeys')
            if unprocessed_keys:
                kwargs['RequestItems'] = unprocessed_keys
            else:
                more_results = False
        offset += BATCH_GET_MAX_ITEMS
    return items


def summarise_dataset(dataset):
    vcf_locations = get_locations(dataset)
    locations_info = get_locations_info(vcf_locations)
    new_locations = set(vcf_locations)

    counts = Counter()
    updated = True
    for location in locations_info:
        vcf_location = location['vcfLocation']['S']
        new_locations.remove(vcf_location)
        if 'toUpdate' in location:
            updated = False
        elif any(count not in location for count in COUNTS):
            new_locations.add(vcf_location)
        elif updated:
            counts.update({count: int(location[count]['N'])
                           for count in COUNTS})

    print('newlocations:', new_locations)
    if new_locations:
        updated = False
    if updated:
        values = {':'+count: {'N': str(counts[count])} for count in COUNTS}
        datasetFilePaths = [out['vcfLocation']['S'] for out in locations_info]
        initDuplicateVariantSearch(dataset, datasetFilePaths)
    else:
        values = {':'+count: {'NULL': True} for count in COUNTS}

    update_dataset(dataset, values)
    for new_location in new_locations:
        summarise_vcf(new_location)


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
    dataset = event['Records'][0]['Sns']['Message']
    summarise_dataset(dataset)
