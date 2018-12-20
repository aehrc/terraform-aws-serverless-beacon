import datetime
import json
import os

import boto3

from api_response import bad_request, bundle_response, missing_parameter

DATASETS_TABLE_NAME = os.environ.get('DATASETS_TABLE')

datasets_table = boto3.resource('dynamodb').Table(DATASETS_TABLE_NAME)


def create_dataset(attributes):
    current_time = get_current_time()
    item = {
        'id': attributes['id'],
        'createDateTime': current_time,
        'updateDateTime': current_time,
        'name': attributes['name'],
        'assemblyId': attributes['assemblyId'],
        'vcfLocations': attributes['vcfLocations'],
        'description': attributes.get('description'),
        'version': attributes.get('version'),
        'externalUrl': attributes.get('externalUrl'),
        'info': attributes.get('info'),
        'dataUseConditions': attributes.get('dataUseConditions'),
    }
    print("Putting Item: {}".format(json.dumps(item)))
    datasets_table.put_item(Item=item)


def get_current_time():
    return datetime.datetime.now().isoformat(timespec='seconds')


def submit_dataset(body_dict, method):
    new = method == 'POST'
    validation_error = validate_request(body_dict, new)
    if validation_error:
        return bad_request(validation_error)
    if new:
        create_dataset(body_dict)
    else:
        update_dataset(body_dict)
    return bundle_response(200, {})


def update_dataset(attributes):
    update_set_expressions = [
        'updateDateTime=:updateDateTime',
    ]
    expression_attribute_values = {
        ':updateDateTime': get_current_time(),
    }
    expression_attribute_names = {}

    if 'name' in attributes:
        update_set_expressions.append('#name=:name')
        expression_attribute_names['#name'] = 'name'
        expression_attribute_values[':name'] = attributes['name']

    if 'assemblyId' in attributes:
        update_set_expressions.append('assemblyId=:assemblyId')
        expression_attribute_values[':assemblyId'] = attributes['assemblyId']

    if 'vcfLocations' in attributes:
        update_set_expressions.append('vcfLocations=:vcfLocations')
        expression_attribute_values[':vcfLocations'] = attributes[
            'vcfLocations']

    if 'description' in attributes:
        update_set_expressions.append('description=:description')
        expression_attribute_values[':description'] = attributes['description']

    if 'version' in attributes:
        update_set_expressions.append('version=:version')
        expression_attribute_values[':version'] = attributes['version']

    if 'externalUrl' in attributes:
        update_set_expressions.append('externalUrl=:externalUrl')
        expression_attribute_values[':externalUrl'] = attributes['externalUrl']

    if 'info' in attributes:
        update_set_expressions.append('info=:info')
        expression_attribute_values[':info'] = attributes['info']

    if 'dataUseConditions' in attributes:
        update_set_expressions.append('dataUseConditions=:dataUseConditions')
        expression_attribute_values[':dataUseConditions'] = attributes[
            'dataUseConditions']

    update_expression = 'SET {}'.format(', '.join(update_set_expressions))
    kwargs = {
        'Key': {
            'id': attributes['id'],
        },
        'UpdateExpression': update_expression,
        'ExpressionAttributeValues': expression_attribute_values,
    }
    if expression_attribute_names:
        kwargs['ExpressionAttributeNames'] = expression_attribute_names
    print("Updating Item: {}".format(json.dumps(kwargs)))

    datasets_table.update_item(**kwargs)


def validate_request(parameters, new):
    try:
        dataset_id = parameters['id']
    except KeyError:
        return missing_parameter('id')
    if not isinstance(dataset_id, str):
        return 'id must be a string'

    if 'name' in parameters:
        if not isinstance(parameters['name'], str):
            return 'name must be a string'
    elif new:
        return missing_parameter('name')

    if 'assemblyId' in parameters:
        if not isinstance(parameters['assemblyId'], str):
            return 'assemblyId must be a string'
    elif new:
        return missing_parameter('assemblyId')

    if 'vcfLocations' in parameters:
        vcf_locations = parameters['vcfLocations']
        if not isinstance(vcf_locations, list):
            return 'vcfLocations must be an array'
        elif not vcf_locations:
            return 'A dataset must have at least one vcf location'
        elif not all(isinstance(loc, str) for loc in vcf_locations):
            return 'Each element in vcfLocations must be a string'
    elif new:
        return missing_parameter('vcfLocations')

    description = parameters.get('description')
    if not isinstance(description, str) and description is not None:
        return 'description must be a string or null'

    version = parameters.get('version')
    if not isinstance(version, str) and version is not None:
        return 'version must be a string or null'

    external_url = parameters.get('externalUrl')
    if not isinstance(external_url, str) and external_url is not None:
        return 'externalUrl must be a string or null'

    info = parameters.get('info')
    if info is not None:
        # This a painful part of the spec - it will be fixed in v1.1.0
        if not isinstance(info, list):
            return 'info must be an array or null'
        elif not all(isinstance(data, dict) for data in info):
            return 'Each element in info must be a key-value object'
        keys = {'key', 'value'}
        if not all(set(data.keys()) == keys
                   and all(isinstance(val, str) for val in data.values())
                   for data in info):
            return ('each object in info must consist of'
                    ' {"key": "key_string", "value": "value_string"}')

    data_use_conditions = parameters.get('dataUseConditions')
    if data_use_conditions is not None:
        if not isinstance(data_use_conditions, dict):
            return 'dataUseConditions must be an object or null'
        if (set(data_use_conditions.keys()) != {'consentCodeDataUse',
                                                'adamDataUse'}
            or not all(isinstance(val, dict)
                       for val in data_use_conditions.values())):
            return ('dataUseConditions object must be in the form:'
                    '{"consentCodeDataUse": {consentCodeDataUse object},'
                    ' "adamDataUse": {ADA-M object}}')
        # Leave the validation of the individual data use objects to the client.

    return ''


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
