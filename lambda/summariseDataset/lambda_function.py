import json
import os

import boto3

VCF_SUMMARIES_TABLE_NAME = os.environ['VCF_SUMMARIES_TABLE']

vcf_summaries_table = boto3.resource('dynamodb').Table(VCF_SUMMARIES_TABLE_NAME)


def summarise_dataset(dataset):
    vcf_locations = dataset['vcfLocations']['L']


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    for dataset in event['Records']:
        dataset_new = dataset['NewImage']
        # Only handle those datasets that have had their vcfLocations changed
        if ('eventName' == 'INSERT'
            or ('eventName' == 'MODIFY'
                and dataset_new['vcfLocations']['L'] != dataset['OldImage'][
                    'vcfLocations']['L'])):
            summarise_dataset(dataset_new)
