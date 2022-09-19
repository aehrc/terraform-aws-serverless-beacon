from collections import Counter, defaultdict
from email.policy import default
from initDuplicateVariantSearch import initDuplicateVariantSearch
import json
import os
import boto3


DATASETS_TABLE_NAME = os.environ['DYNAMO_DATASETS_TABLE']
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
        'ProjectionExpression': 'vcfLocations,vcfGroups',
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
    
    vcf_locations = response['Items'][0].get('vcfLocations', {}).get('SS', [])
    vcf_groups = [grp['SS'] for grp in response['Items'][0].get('vcfGroups', {}).get('L', [])]
    
    return vcf_locations, vcf_groups


def get_locations_info(locations):
    # locations are the keys in VCF_SUMMARIES_TABLE_NAME
    items = []
    num_locations = len(locations)
    offset = 0
    # project fields that needs to be updated/or have been updated
    kwargs = {
        'RequestItems': {
            VCF_SUMMARIES_TABLE_NAME: {
                'ProjectionExpression': ('vcfLocation,toUpdate,'
                                         + ','.join(COUNTS)),
                'Keys': [],
            },
        },
    }
    # retrieve batches with batch size upto BATCH_GET_MAX_ITEMS
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
        # retrieve items with batch_get_item
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
    # sample counting must be done once and only once per vcf group
    # assumption: all vcf in a group has the same samples 
    # (i.e. VCFs are split only by chromosomes or a group of chromosomes, not samples)
    vcf_locations, vcf_groups = get_locations(dataset)
    locations_info = get_locations_info(vcf_locations)
    new_locations = set(vcf_locations)
    # create an id for each vcf group for identification
    vcf_to_group_map = {loc: idx for idx, grp in enumerate(vcf_groups) for loc in grp}
    # records if the vcf group is counted once
    vcf_group_counted = defaultdict(lambda: False)

    counts = Counter()
    updated = True

    for location in locations_info:
        vcf_location = location['vcfLocation']['S']
        new_locations.remove(vcf_location)
        # the vcf summary is yet to be updated
        # TODO use the variable value instead of in keyword (ORM support)
        if 'toUpdate' in location:
            updated = False
        # if counts are not computed for the vcf
        elif any(count not in location for count in COUNTS):
            new_locations.add(vcf_location)
        # if the vcf is updated
        elif updated:
            # increment the counts using each vcf location to get total counts
            counts.update({count: int(location[count]['N'])
                           for count in COUNTS if count != 'sampleCount'})
            
            # get the group id of vcf location
            vcf_group = vcf_to_group_map[vcf_location]
            # if the group's sample count is not recorded
            # update counter and flag group as recorded
            if not vcf_group_counted[vcf_group]:
                counts.update({'sampleCount': int(location['sampleCount']['N'])})
                vcf_group_counted[vcf_group] = True

    print('newlocations:', new_locations)
    # if there are new locations updated=False
    if new_locations:
        updated = False
    # if the dataset is updated (all vcfs summarised)
    if updated:
        values = {':' + count: {'N': str(counts[count])} for count in COUNTS}
        datasetFilePaths = [out['vcfLocation']['S'] for out in locations_info]
        # start duplicate variant search, once after all updates are done
        # this is only to count the unique variants
        initDuplicateVariantSearch(dataset, datasetFilePaths)
    else:
        # this will be {':callCount': {'NULL': True}, ':sampleCount': {'NULL': True}}
        values = {':' + count: {'NULL': True} for count in COUNTS}

    # update the dataset record
    update_dataset(dataset, values, new_locations)
    # summarise each of the vcf file
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


def update_dataset(dataset_id, values, new_locations):
    # update the counts in DATASETS_TABLE_NAME
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
    # if new locations are there, put them in the DATASETS_TABLE_NAME
    if new_locations:
        kwargs['UpdateExpression'] += ', toUpdateFiles=:toUpdateFiles'
        kwargs['ExpressionAttributeValues'][':toUpdateFiles'] = {
            'SS': list(new_locations),
        }
    print('Updating item: {}'.format(json.dumps(kwargs)))
    dynamodb.update_item(**kwargs)


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    # only dataset id is received
    dataset = event['Records'][0]['Sns']['Message']
    summarise_dataset(dataset)


if __name__ == '__main__':
    pass
