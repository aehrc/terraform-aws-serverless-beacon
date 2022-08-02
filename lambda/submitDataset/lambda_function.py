import datetime
import json
import os
import subprocess
from jsonschema import Draft7Validator

import boto3

from api_response import bad_request, bundle_response

DATASETS_TABLE_NAME = os.environ['DATASETS_TABLE']
SUMMARISE_DATASET_SNS_TOPIC_ARN = os.environ['SUMMARISE_DATASET_SNS_TOPIC_ARN']

# uncomment below for debugging
# os.environ['LD_DEBUG'] = 'all'

dynamodb = boto3.client('dynamodb')
sns = boto3.client('sns')

newSchema = json.load(open("new-schema.json"))
updateSchema = json.load(open("update-schema.json"))


# just checking if the tabix would work as expected on a valid vcf.gz file
# validate if the index file exists too
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

    vcfGroups = attributes.get('vcfGroups')
    if vcfGroups:
        item['vcfGroups'] = {
            'L': [{ 'SS': vcfGroup } for vcfGroup in attributes['vcfGroups']]
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
    d = datetime.datetime.now(datetime.timezone.utc)
    return d.strftime('%Y-%m-%dT%H:%M:%S.%f%z')


def submit_dataset(body_dict, method):
    new = method == 'POST'
    validation_error = validate_request(body_dict, new)
    if validation_error:
        return bad_request(validation_error)

    if 'vcfLocations' in body_dict:
        # validate vcf files if skipCheck is not specified 
        if 'skipCheck' not in body_dict:
            errors = check_vcf_locations(body_dict['vcfLocations'])
            if errors:
                return bad_request(errors)
        summarise = True
    else:
        summarise = False
    # handle data set submission or update
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
    
    if 'vcfGroups' in attributes:
        update_set_expressions.append('vcfGroups=:vcfGroups')
        expression_attribute_values[':vcfGroups'] = {
            'L': [{ 'SS': vcfGroup } for vcfGroup in attributes['vcfGroups']]
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
    validator = None
    # validate request body with schema for a new submission or update
    if new:
        validator = Draft7Validator(newSchema)
    else:
        validator = Draft7Validator(updateSchema)

    errors = sorted(validator.iter_errors(parameters), key=lambda e: e.path)
    return [error.message for error in errors]


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
