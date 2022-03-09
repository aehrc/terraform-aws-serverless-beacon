import json
import os
import queue
import re
import threading

import boto3

from api_response import bad_request, bundle_response, missing_parameter
from chrom_matching import CHROMOSOMES, get_matching_chromosome, get_vcf_chromosomes

BEACON_ID = os.environ['BEACON_ID']
DATASETS_TABLE_NAME = os.environ['DATASETS_TABLE']
SPLIT_QUERY = os.environ['SPLIT_QUERY_LAMBDA']

INCLUDE_DATASETS_VALUES = {
    'ALL',
    'HIT',
    'MISS',
    'NONE',
}

os.environ['PATH'] += ':' + os.environ['LAMBDA_TASK_ROOT']

base_pattern = re.compile('[ACGT]+|N')

dynamodb = boto3.client('dynamodb')
aws_lambda = boto3.client('lambda')


def get_datasets(assembly_id, dataset_ids):
    items = []
    kwargs = {
        'TableName': 'Datasets',
        'IndexName': 'assembly_index',
        'ProjectionExpression': 'id,vcfLocations,vcfGroups',
        'KeyConditionExpression': 'assemblyId = :assemblyId',
        'ExpressionAttributeValues': {
            ':assemblyId': {'S': assembly_id}
        }
    }
    more_results = True
    while more_results:
        print("Querying table: {}".format(json.dumps(kwargs)))
        response = dynamodb.query(**kwargs)
        print("Received response: {}".format(json.dumps(response)))
        items += response.get('Items', [])
        last_evaluated = response.get('LastEvaluatedKey', {})
        if last_evaluated:
            kwargs['ExclusiveStartKey'] = last_evaluated
        else:
            more_results = False
    if dataset_ids:
        items = [i for i in items if i['id']['S'] in dataset_ids]
    return items


def get_vcf_chromosome_map(datasets, chromosome):
    all_vcfs = list(set(loc for d in datasets for loc in d['vcfLocations']['SS']))
    vcf_chromosome_map = {}
    for vcf in all_vcfs:
        vcf_chromosomes = get_vcf_chromosomes(vcf)
        vcf_chromosome_map[vcf] = get_matching_chromosome(vcf_chromosomes,
                                                          chromosome)
    return vcf_chromosome_map


def perform_query(dataset_id, vcf_locations, vcf_groups, reference_bases, region_start,
                  region_end, end_min, end_max, alternate_bases, variant_type,
                  include_datasets, responses):

    payload = json.dumps({
        'dataset_id': dataset_id,
        'reference_bases': reference_bases,
        'region_start': region_start,
        'region_end': region_end,
        'end_min': end_min,
        'end_max': end_max,
        'alternate_bases': alternate_bases,
        'variant_type': variant_type,
        'include_datasets': include_datasets,
        'vcf_locations': vcf_locations,
        'vcf_groups': vcf_groups,
    })
    print("Invoking {lambda_name} with payload: {payload}".format(
        lambda_name=SPLIT_QUERY, payload=payload))
    response = aws_lambda.invoke(
        FunctionName=SPLIT_QUERY,
        Payload=payload,
    )
    response_json = response['Payload'].read()
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

    reference_name = parameters['referenceName']
    vcf_chromosomes = get_vcf_chromosome_map(datasets, reference_name)
    start = parameters.get('start')
    if start is None:
        region_start = parameters['startMin']
        region_end = parameters['startMax']
        end_min = parameters['endMin']
        end_max = parameters['endMax']
    else:
        region_start = region_end = start
        end = parameters.get('end')
        if end is None:
            end = start
        end_min = end_max = end
    reference_bases = parameters['referenceBases']
    # account for the 1-based indexing of vcf files
    region_start += 1
    region_end += 1
    end_min += 1
    end_max += 1
    if reference_bases != 'N':
        # For specific reference bases region may be smaller
        max_offset = len(reference_bases) - 1
        end_max = min(region_end + max_offset, end_max)
        region_start = max(end_min - max_offset, region_start)
        if end_min > end_max or region_start > region_end:
            # Region search will find nothing, search a dummy region
            region_start = 2000000000
            region_end = region_start
            end_min = region_start + max_offset
            end_max = end_min
    alternate_bases = parameters.get('alternateBases')
    variant_type = parameters.get('variantType')
    include_datasets = parameters.get('includeDatasetResponses', 'NONE')
    responses = queue.Queue()
    threads = []
    for dataset in datasets:
        dataset_id = dataset['id']['S']
        vcf_locations = {vcf: vcf_chromosomes[vcf]
                         for vcf in dataset['vcfLocations']['SS']
                         if vcf_chromosomes[vcf]}
        # record vcf grouping information using the relevant vcf files
        vcf_groups = [grp for grp in [
                                    [loc for loc in vcfg["SS"] if loc in vcf_locations]
                                         for vcfg in dataset['vcfGroups']['L']
                                 ] if len(grp) > 0]

        t = threading.Thread(target=perform_query,
                             kwargs={
                                 'dataset_id': dataset_id,
                                 'vcf_locations': vcf_locations,
                                 'vcf_groups': vcf_groups,
                                 'reference_bases': reference_bases,
                                 'region_start': region_start,
                                 'region_end': region_end,
                                 'end_min': end_min,
                                 'end_max': end_max,
                                 'alternate_bases': alternate_bases,
                                 'variant_type': variant_type,
                                 'include_datasets': include_datasets,
                                 'responses': responses,
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
        exists = exists or response['exists']
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

    start = parameters.get('start')
    if start is None:
        missing_parameters.add('start')
    elif not isinstance(start, int):
            return "start must be an integer"

    end = parameters.get('end')
    if end is None:
        missing_parameters.add('end')
        if 'start' not in missing_parameters and reference_bases == 'N':
            return ("referenceBases must be [ACGT]* if start is specified but"
                    " end is not specified")
    else:
        if 'start' in missing_parameters:
            return "end may not be specified if start is not specified"
        if not isinstance(end, int):
            return "end must be an integer"

    start_min = parameters.get('startMin')
    if start_min is None:
        if 'start' in missing_parameters:
            return missing_parameter('start', 'startMin')
        missing_parameters.add('startMin')
    else:
        if 'start' not in missing_parameters:
            return "Only one of start and startMin may be specified"
        if not isinstance(start_min, int):
            return "startMin must be an integer"

    start_max = parameters.get('startMax')
    if start_max is None:
        if 'start' in missing_parameters:
            return "If startMin is specified, startMax must also be specified"
        missing_parameters.add('startMax')
    elif not isinstance(start_max, int):
        return "startMax must be an integer"

    end_min = parameters.get('endMin')
    if end_min is None:
        if 'start' in missing_parameters:
            return "If startMin is specified, endMin must also be specified"
        missing_parameters.add('endMin')
    elif not isinstance(end_min, int):
        return "endMin must be an integer"

    end_max = parameters.get('endMax')
    if end_max is None:
        if 'start' in missing_parameters:
            return "If startMax is specified, endMax must also be specified"
        missing_parameters.add('endMax')
    elif not isinstance(end_max, int):
        return "endMax must be an integer"

    alternate_bases = parameters.get('alternateBases')
    if alternate_bases is None:
        missing_parameters.add('alternateBases')
    else:
        if not isinstance(alternate_bases, str):
            return "alternateBases must be a string"
        if not base_pattern.fullmatch(alternate_bases):
            return "alternateBases must be either [ACGT]* or N"

    variant_type = parameters.get('variantType')
    if variant_type is None:
        if 'alternateBases' in missing_parameters:
            return missing_parameter('alternateBases', 'variantType')
        missing_parameters.add('variantType')

    dataset_ids = parameters.get('datasetIds')
    if dataset_ids is None:
        missing_parameters.add('datasetIds')
    else:
        if not isinstance(dataset_ids, list):
            return "datasetIds must be an array"
        if not all(isinstance(dataset_id, str) for dataset_id in dataset_ids):
            return "datasetIds must be an array of strings"

    include_datasets = parameters.get('includeDatasetResponses')
    if include_datasets is None:
        missing_parameters.add('includeDatasetResponses')
    elif include_datasets not in INCLUDE_DATASETS_VALUES:
        return "includeDatasetResponses must be one of {}".format(
            ', '.join(INCLUDE_DATASETS_VALUES))

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
        for int_field in ('start', 'end', 'startMin', 'startMax', 'endMin',
                          'endMax'):
            if int_field in parameters:
                try:
                    parameters[int_field] = int(parameters[int_field])
                except ValueError:
                    # Cannot be formatted as an integer, handle in validation
                    pass
    return query_datasets(parameters)
