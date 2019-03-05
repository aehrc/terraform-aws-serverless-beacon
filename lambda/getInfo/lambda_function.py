import json
import os

import boto3

from api_response import bundle_response

BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']
BEACON_NAME = os.environ['BEACON_NAME']
DATASETS_TABLE = os.environ['DATASETS_TABLE']
ORGANISATION_ID = os.environ['ORGANISATION_ID']
ORGANISATION_NAME = os.environ['ORGANISATION_NAME']

dynamodb = boto3.client('dynamodb')


def get_info():
    datasets_table_data = scan_datasets_table()
    transformed_data = transform_data(datasets_table_data)
    bundled_response = bundle_response(200, transformed_data)
    return bundled_response


def scan_datasets_table():
    items = []
    kwargs = {
        'TableName': DATASETS_TABLE,
        'ProjectionExpression': 'id,#name,assemblyId,createDateTime,'
                                'updateDateTime,description,version,'
                                'variantCount,callCount,sampleCount,'
                                'externalUrl,info,dataUseConditions',
        'ExpressionAttributeNames': {
            '#name': 'name',
        }
    }
    more_results = True
    while more_results:
        print("Scanning table: {}".format(json.dumps(kwargs)))
        response = dynamodb.scan(**kwargs)
        print("Received response: {}".format(json.dumps(response)))
        items += response.get('Items', [])
        last_evaluated = response.get('LastEvaluatedKey', {})
        if last_evaluated:
            kwargs['ExclusiveStartKey'] = last_evaluated
        else:
            more_results = False
    return items


def transform_data(items):
    return {
        "id": BEACON_ID,
        "name": BEACON_NAME,
        "apiVersion": BEACON_API_VERSION,
        "organization": {
            "id": ORGANISATION_ID,
            "name": ORGANISATION_NAME
        },
        "datasets": [
            {
                "id": item['id']['S'],
                "name": item['name']['S'],
                "assemblyId": item['assemblyId']['S'],
                "createDateTime": item['createDateTime']['S'],
                "updateDateTime": "$item.updateDateTime.S",
                "description": item.get('description', {}).get('S') or None,
                "version": item.get('version', {}).get('S') or None,
                "variantCount": item.get('variantCount', {}).get('N') or None,
                "callCount": item.get('callCount', {}).get('N') or None,
                "sampleCount": item.get('sampleCount', {}).get('N') or None,
                "info": item.get('info', {}).get('L') or None,
                "dataUseConditions": item.get('dataUseConditions', {}
                                              ).get('M') or None,
                "externalUrl": item.get('externalUrl', {}).get('S') or None,
            } for item in items
        ]
    }


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    response = get_info()
    print('Returning Response: {}'.format(json.dumps(response)))
    return response
