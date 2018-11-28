import datetime
import json
import os

import boto3

HEADERS = {"Access-Control-Allow-Origin": "*"}
DATASETS_TABLE_NAME = os.environ.get('DATASETS_TABLE')

datasets_table = boto3.resource('dynamodb').Table(DATASETS_TABLE_NAME)


def bundle_response(status_code, body):
    return {
            'statusCode': status_code,
            'headers': HEADERS,
            'body': json.dumps(body),
    }


def create_dataset(attributes):
    current_time = get_current_time()
    attributes['createDateTime'] = current_time
    attributes['updateDateTime'] = current_time
    print("Putting Item: {}".format(json.dumps(attributes)))
    datasets_table.put_item(Item=attributes)


def get_current_time():
    return datetime.datetime.now().isoformat(timespec='seconds')


def submit_dataset(body_dict, method):
    new = method == 'POST'
    attributes = {}
    try:
        dataset_id = body_dict['id']
    except KeyError:
        return bundle_response(400, {
            'data': 'id must be present in request body.',
        })
    if not isinstance(dataset_id, str):
        return bundle_response(400, {
            'data': 'id must be a string.',
        })
    else:
        attributes['id'] = dataset_id

    try:
        name = body_dict['name']
    except KeyError:
        if new:
            return bundle_response(400, {
                'data': 'name must be present in request body.',
            })
    else:
        if not isinstance(name, str):
            return bundle_response(400, {
                'data': 'name must be a string.',
            })
        else:
            attributes['datasetName'] = name

    try:
        assembly_id = body_dict['assemblyId']
    except KeyError:
        if new:
            return bundle_response(400, {
                'data': 'assemblyId must be present in request body.',
            })
    else:
        if not isinstance(assembly_id, str):
            return bundle_response(400, {
                'data': 'assemblyId must be a string.',
            })
        else:
            attributes['assemblyId'] = assembly_id

    try:
        description = body_dict['description']
    except KeyError:
        if new:
            attributes['description'] = None
    else:
        if description:
            if not isinstance(description, str):
                return bundle_response(400, {
                    'data': 'description must be a string.',
                })
            else:
                attributes['assemblyId'] = description
        else:
            attributes['description'] = None


def update_dataset(attributes):
    attributes['updateDateTime'] = get_current_time()


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    event_body = event.get('body')
    if not event_body:
        return bundle_response(400, {'data': 'No body sent with request.'})
    try:
        body_dict = json.loads(event_body)
    except ValueError:
        return bundle_response(400, {
            'data': 'Error parsing request body, Expected JSON.',
        })
    method = event['httpMethod']
    return submit_dataset(body_dict, method)
