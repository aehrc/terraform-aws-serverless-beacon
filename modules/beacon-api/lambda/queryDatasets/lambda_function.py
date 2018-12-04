import json
import os
import re

import boto3

from api_response import bad_request, bundle_response

HEADERS = {"Access-Control-Allow-Origin": "*"}
DATASETS_TABLE_NAME = os.environ.get('DATASETS_TABLE')


CHROMOSOMES = [
    '1',
    '2',
    '3',
    '4',
    '5',
    '6',
    '7',
    '8',
    '9',
    '10',
    '11',
    '12',
    '13',
    '14',
    '15',
    '16',
    '17',
    '18',
    '19',
    '20',
    '21',
    '22',
    '23',
    'X',
    'Y',
    'MT',
]
base_pattern = re.compile('[ACGT]+|N')

datasets_table = boto3.resource('dynamodb').Table(DATASETS_TABLE_NAME)


def missing_parameter(*parameters):
    if len(parameters) > 1:
        required = "one of {}".format(','.join(parameters))
    else:
        required = parameters[0]
    return "Must include {}".format(required)


def query_datasets(parameters):
    validation_error = validate_request(parameters)
    if validation_error:
        return bad_request(validation_error)


def validate_request(parameters):
    missing_parameters = set()
    try:
        reference_name = parameters['referenceName']
    except KeyError:
        return missing_parameter('referenceName')
    if not isinstance(reference_name, str):
        return "referenceName must be a string"
    if reference_name not in CHROMOSOMES:
        return "referenceName must be one of {}".format(','.join(CHROMOSOMES))

    try:
        reference_bases = parameters['referenceBases']
    except KeyError:
        return missing_parameter('referenceBases')
    if not isinstance(reference_name, str):
        return "referenceBases must be a string"
    if not base_pattern.fullmatch(reference_bases):
        return "referenceBases must be either [ACGT]* or N"

    try:
        assembly_id = parameters['assemblyId']
    except KeyError:
        return missing_parameter('assemblyId')
    if not isinstance(assembly_id, str):
        return "assemblyId must be a string"

    try:
        start = parameters['start']
    except KeyError:
        missing_parameters.add('start')
    return ''


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    if event['httpMethod'] == 'POST':
        event_body = event.get('body')
        if not event_body:
            return bad_request('No body sent with request.')
        try:
            parameters = json.loads(event_body)
        except ValueError:
            return bad_request('Error parsing request body, Expected JSON.')
    else:  # method == 'GET'
        parameters = event['queryStringParameters']
        parameters.update(event.get('multiValueQueryStringParameters'), {})
    return query_datasets(parameters)
