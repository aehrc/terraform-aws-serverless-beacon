import datetime
import json
import os
import subprocess

import boto3

from api_response import bad_request, bundle_response, missing_parameter

DATASETS_TABLE_NAME = os.environ['DATASETS_TABLE']
SUMMARISE_DATASET_SNS_TOPIC_ARN = os.environ['SUMMARISE_DATASET_SNS_TOPIC_ARN']

os.environ['PATH'] += ':' + os.environ['LAMBDA_TASK_ROOT']

dynamodb = boto3.client('dynamodb')
sns = boto3.client('sns')


def check_vcf_locations(locations):
    errors = []
    for location in locations:
        try:
            subprocess.check_output(
                args=[
                    'tabix',
                    '--list-chroms',
                    location,
                ],
                stderr=subprocess.PIPE,
                cwd='/tmp',
                encoding='utf-8',
            )
        except subprocess.CalledProcessError as e:
            error_message = e.stderr
            print("cmd {} returned non-zero error code {}. stderr:\n{}".format(
                e.cmd, e.returncode, error_message
            ))
            if error_message.startswith("[E::hts_open_format] Failed to open"):
                errors.append("Could not access {}.".format(location))
            elif error_message.startswith("[E::hts_hopen] Failed to open"):
                errors.append("{} is not a gzipped vcf file.".format(location))
            elif error_message.startswith("Could not load .tbi index"):
                errors.append("Could not open index file for {}.".format(
                    location))
            else:
                raise e
    return "\n".join(errors)


def create_dataset(attributes):
    current_time = get_current_time()
    item = {
        'id': {
            'S': attributes['id'],
        },
        'createDateTime': {
            'S': current_time,
        },
        'updateDateTime': {
            'S': current_time,
        },
        'name': {
            'S': attributes['name'],
        },
        'assemblyId': {
            'S': attributes['assemblyId'],
        },
        'vcfLocations': {
            'SS': attributes['vcfLocations'],
        },
    }

    description = attributes.get('description')
    if description:
        item['description'] = {
            'S': description,
        }

    version = attributes.get('version')
    if version:
        item['version'] = {
            'S': version,
        }

    external_url = attributes.get('externalUrl')
    if external_url:
        item['externalUrl'] = {
            'S': external_url,
        }

    info = attributes.get('info')
    if info:
        item['info'] = {
            'M': info,
        }

    data_use_conditions = attributes.get('dataUseConditions')
    if data_use_conditions:
        item['dataUseConditions'] = {
            'M': data_use_conditions,
        }

    kwargs = {
        'TableName': DATASETS_TABLE_NAME,
        'Item': item,
    }

    print("Putting item in table: {}".format(json.dumps(kwargs)))
    dynamodb.put_item(**kwargs)


def get_current_time():
    return datetime.datetime.now().isoformat(timespec='seconds')


def submit_dataset(body_dict, method):
    new = method == 'POST'
    validation_error = validate_request(body_dict, new)
    if validation_error:
        return bad_request(validation_error)
    if 'vcfLocations' in body_dict:
        if 'skipCheck' not in body_dict:
            errors = check_vcf_locations(body_dict['vcfLocations'])
            if errors:
                return bad_request(errors)
        summarise = True
    else:
        summarise = False
    if new:
        create_dataset(body_dict)
    else:
        update_dataset(body_dict)
    if summarise:
        summarise_dataset(body_dict['id'])
    return bundle_response(200, {})


def summarise_dataset(dataset):
    kwargs = {
        'TopicArn': SUMMARISE_DATASET_SNS_TOPIC_ARN,
        'Message': dataset
    }
    print('Publishing to SNS: {}'.format(json.dumps(kwargs)))
    response = sns.publish(**kwargs)
    print('Received Response: {}'.format(json.dumps(response)))


def update_dataset(attributes):
    update_set_expressions = [
        'updateDateTime=:updateDateTime',
    ]
    expression_attribute_values = {
        ':updateDateTime': {
            'S': get_current_time(),
        }
    }
    expression_attribute_names = {}

    if 'name' in attributes:
        update_set_expressions.append('#name=:name')
        expression_attribute_names['#name'] = 'name'
        expression_attribute_values[':name'] = {
            'S': attributes['name'],
        }

    if 'assemblyId' in attributes:
        update_set_expressions.append('assemblyId=:assemblyId')
        expression_attribute_values[':assemblyId'] = {
            'S': attributes['assemblyId'],
        }

    if 'vcfLocations' in attributes:
        update_set_expressions.append('vcfLocations=:vcfLocations')
        expression_attribute_values[':vcfLocations'] = {
            'SS': attributes['vcfLocations'],
        }

    if 'description' in attributes:
        update_set_expressions.append('description=:description')
        expression_attribute_values[':description'] = {
            'S': attributes['description'],
        }

    if 'version' in attributes:
        update_set_expressions.append('version=:version')
        expression_attribute_values[':version'] = {
            'S': attributes['version'],
        }

    if 'externalUrl' in attributes:
        update_set_expressions.append('externalUrl=:externalUrl')
        expression_attribute_values[':externalUrl'] = {
            'S': attributes['externalUrl'],
        }

    if 'info' in attributes:
        update_set_expressions.append('info=:info')
        expression_attribute_values[':info'] = {
            'L': attributes['info'],
        }

    if 'dataUseConditions' in attributes:
        update_set_expressions.append('dataUseConditions=:dataUseConditions')
        expression_attribute_values[':dataUseConditions'] = {
            'M': attributes['dataUseConditions'],
        }

    update_expression = 'SET {}'.format(', '.join(update_set_expressions))
    kwargs = {
        'TableName': DATASETS_TABLE_NAME,
        'Key': {
            'id': {
                'S': attributes['id'],
            },
        },
        'UpdateExpression': update_expression,
        'ExpressionAttributeValues': expression_attribute_values,
    }
    if expression_attribute_names:
        kwargs['ExpressionAttributeNames'] = expression_attribute_names
    print("Updating table: {kwargs}".format(kwargs=json.dumps(kwargs)))

    dynamodb.update_item(**kwargs)


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
