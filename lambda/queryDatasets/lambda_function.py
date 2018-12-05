import json
import os
import math
import queue
import re
import threading

import boto3

from api_response import bad_request, bundle_response

BEACON_ID = os.environ.get('BEACON_ID')
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

dynamodb = boto3.client('dynamodb')
aws_lambda = boto3.client('lambda')


def get_datasets(assembly_id, dataset_ids):
    items = []
    kwargs = {
        'TableName': 'Datasets',
        'IndexName': 'assembly_index',
        'ProjectionExpression': 'id,vcfLocation',
        'KeyConditionExpression': 'assemblyId = :assemblyId',
        'ExpressionAttributeValues': {
            ':assemblyId': {'S': assembly_id}
        }
    }
    if dataset_ids:
        dataset_expression = '({})'.format(
            ' OR '.join(
                'id = {}'.format(d) for d in dataset_ids
            )
        )
        kwargs['KeyConditionExpression'] += ' AND {}'.format(dataset_expression)
        kwargs['ExpressionAttributeValues'].update({
            ':'+d: {'S': d} for d in dataset_ids
        })
    more_results = True
    while more_results:
        response = dynamodb.query(**kwargs)
        items += response.get('Items', [])
        last_evaluated = response.get('LastEvaluatedKey', {})
        if last_evaluated:
            kwargs['ExclusiveStartKey'] = last_evaluated
        else:
            more_results = False
    return items


def missing_parameter(*parameters):
    if len(parameters) > 1:
        required = "one of {}".format(','.join(parameters))
    else:
        required = parameters[0]
    return "Must include {}".format(required)


def perform_query(dataset, responses, include_datasets):
    dataset_id = dataset['id']['S']
    payload = json.dumps({
        'dataset_id': dataset_id,
        'include_datasets': include_datasets,
        'vcf_location': dataset['vcfLocation'],
    })
    print("Invoking performQuery with payload: {}".format(payload))
    response = aws_lambda.invoke(
        FunctionName='performQuery',
        InvocationType='RequestResponse',
        ClientContext='string',
        Payload=payload,
    )
    response_json = response['Payload']
    print("dataset_id {ds} received payload: {p}".format(ds=dataset_id,
                                                         p=response_json))
    response_dict = json.loads(response_json)
    responses.put(response_dict)


def query_datasets(parameters):
    response_dict = {
        'beaconId': BEACON_ID,
        'apiVersion': None,
        'alleleRequest': parameters,
    }
    validation_error = validate_request(parameters)
    if validation_error:
        return bad_request(validation_error, response_dict)

    datasets = get_datasets(parameters['assemblyId'],
                            parameters.get('datasetIds'))
    include_datasets = parameters.get('includeDatasetResponses', 'NONE')
    responses = queue.Queue()
    threads = []
    for dataset in datasets:
        t = threading.Thread(target=perform_query,
                             kwargs={
                                 'dataset': dataset,
                                 'responses': responses,
                                 'include_dataset': include_datasets,
                             })
        t.start()
        threads.append(t)
    num_threads = len(threads)
    processed = 0
    dataset_responses = []
    exists = False
    while processed < num_threads and (include_datasets != 'NONE'
                                       or not exists):
        response = responses.get()
        processed += 1
        if 'exists' not in response:
            # function errored out, ignore
            continue
        exists = exists and response['exists']
        if response.pop('include'):
            dataset_responses.append(response)
    response_dict.update({
        'exists': exists,
        'datasetAlleleResponses': dataset_responses or None,
    })
    return bundle_response(200, response_dict)


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
    # TODO Add more validation
    return ''


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    extra_params = {
        'beaconId': BEACON_ID,
    }
    if event['httpMethod'] == 'POST':
        event_body = event.get('body')
        if not event_body:
            return bad_request('No body sent with request.', extra_params)
        try:
            parameters = json.loads(event_body)
        except ValueError:
            return bad_request('Error parsing request body, Expected JSON.',
                               extra_params)
    else:  # method == 'GET'
        parameters = event['queryStringParameters']
        if not parameters:
            return bad_request('No query parameters sent with request.',
                               extra_params)
        multi_values = event['multiValueQueryStringParameters']
        parameters['datasetIds'] = multi_values.get('datasetIds')
    return query_datasets(parameters)
