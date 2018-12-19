import datetime
import json
import os

import boto3

from api_response import bad_request, bundle_response

DATASETS_TABLE_NAME = os.environ.get('DATASETS_TABLE')
UPDATE_DATASET_SNS_TOPIC_ARN = os.environ.get('UPDATE_DATASET_SNS_TOPIC_ARN')

datasets_table = boto3.resource('dynamodb').Table(DATASETS_TABLE_NAME)
update_sns_topic = boto3.resource('sns').Topic(UPDATE_DATASET_SNS_TOPIC_ARN)

types = {
    'string': {
        'type': str,
        'prefix': 'a',
        'aws': 'S',
    },
    'array': {
        'type': list,
        'prefix': 'an',
        'aws': 'L',
    },
    'object': {
        'type': dict,
        'prefix': 'an',
        'aws': 'M',
    },
}

attribute_details = {
    'id': {
        'type': 'string',
        'required': True,
    },
    'name': {
        'alt_name': 'datasetName',
        'type': 'string',
        'required': True,
    },
    'assemblyId': {
        'type': 'string',
        'required': True,
    },
    'vcfLocations': {
        'type': 'array',
        'required': True,
    },
    'description': {
        'type': 'string',
        'required': False,
    },
    'version': {
        'type': 'string',
        'required': False,
    },
    'externalUrl': {
        'type': 'string',
        'required': False,
    },
    'info': {
        'type': 'array',
        'required': False,
    },
    'dataUseConditions': {
        'type': 'object',
        'required': False,
    },
    # To be added by the function
    'createDateTime': {
        'type': 'string',
        'required': False,
    },
    'updateDateTime': {
        'type': 'string',
        'required': False,
    },
}


def create_dataset(attributes):
    current_time = get_current_time()
    attributes['createDateTime'] = current_time
    attributes['updateDateTime'] = current_time
    print("Putting Item: {}".format(json.dumps(attributes)))
    datasets_table.put_item(Item=attributes)


def get_current_time():
    return datetime.datetime.now().isoformat(timespec='seconds')


def publish_sns(dataset_id):
    event_json = json.dumps({'id': dataset_id})
    print("Publishing SNS Event: {}".format(event_json))
    update_sns_topic.publish(
        MessageStructure='json',
        Message=json.dumps({
            'default': event_json,
        }),
    )


def submit_dataset(body_dict, method):
    new = method == 'POST'
    attributes = {}
    for attribute, details in attribute_details.items():
        try:
            dataset_attr = body_dict[attribute]
        except KeyError:
            if new or attribute == 'id':
                if details['required']:
                    return bad_request('{} must be present in request'
                                       ' body.'.format(attribute))
                else:
                    attributes[attribute] = None
        else:
            if dataset_attr:
                type_string = details['type']
                type_dict = types[type_string]
                if isinstance(dataset_attr, type_dict['type']):
                    attributes[attribute] = dataset_attr
                else:
                    return bad_request('{} must be {} {}.'.format(
                        attribute, type_dict['prefix'], type_string))
            else:
                attributes['id'] = None
    if new:
        create_dataset(attributes)
    else:
        update_dataset(attributes)
    publish_sns(attributes['id'])
    return bundle_response(200, {})


def update_dataset(attributes):
    attributes['updateDateTime'] = get_current_time()
    if 'createDateTime' in attributes:
        del attributes['createDateTime']
    print("Updating Item: {}".format(json.dumps(attributes)))

    datasets_table.update_item(
        Key={'id': attributes['id']},
        UpdateExpression='SET {}'.format(','.join(
            '{alt}=:{at}'.format(alt=attribute_details[at].get('alt_name', at),
                                 at=at) for at in attributes if at != 'id'
        )),
        ExpressionAttributeValues={
            ':{at}'.format(at=at): val
            for at, val in attributes.items() if at != 'id'
        }
    )


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    event_body = event.get('body')
    if not event_body:
        return bad_request('No body sent with request.')
    try:
        body_dict = json.loads(event_body)
    except ValueError:
        return bad_request('Error parsing request body, Expected JSON.')
    method = event['httpMethod']
    return submit_dataset(body_dict, method)
