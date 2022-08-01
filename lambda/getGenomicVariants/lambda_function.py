import json
import os
import jsonschema
import boto3
import queue
import threading

from api_response import bundle_response, bad_request
from chrom_matching import CHROMOSOMES, get_matching_chromosome, get_vcf_chromosomes
import responses
import entries

BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']
DATASETS_TABLE_NAME = os.environ['DATASETS_TABLE']
SPLIT_QUERY = os.environ['SPLIT_QUERY_LAMBDA']

requestSchemaJSON = json.load(open("requestParameters.json"))

dynamodb = boto3.client('dynamodb')
aws_lambda = boto3.client('lambda')


def split_query(dataset_id, vcf_locations, vcf_groups, reference_bases, region_start,
                  region_end, end_min, end_max, alternate_bases, variant_type,
                  include_datasets, requested_granularity, responses):

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
        'requested_granularity': requested_granularity
    })
    print(f"Invoking {SPLIT_QUERY} with payload: {payload}")
    response = aws_lambda.invoke(
        FunctionName=SPLIT_QUERY,
        Payload=payload,
    )
    response_json = response['Payload'].read()
    print(f"dataset_id {dataset_id} received payload: {response_json}")
    response_dict = json.loads(response_json)
    responses.put(response_dict)


def get_vcf_chromosome_map(datasets, chromosome):
    all_vcfs = list(set(loc for d in datasets for loc in d['vcfLocations']['SS']))
    vcf_chromosome_map = {}
    for vcf in all_vcfs:
        vcf_chromosomes = get_vcf_chromosomes(vcf)
        vcf_chromosome_map[vcf] = get_matching_chromosome(vcf_chromosomes,
                                                          chromosome)
    return vcf_chromosome_map


def get_datasets(assembly_id, dataset_ids=None):
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
    # TODO support more advanced querying
    if dataset_ids:
        items = [i for i in items if i['id']['S'] in dataset_ids]
    return items


def get_analyses(event):
    print(event)
    response = responses.result_sets_response
    # response = responses.counts_response
    # response = responses.boolean_response

    return bundle_response(200, response)


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))

    if (event['httpMethod'] == 'GET'):
        params = event['queryStringParameters']
        print(f"Query params {params}")
        apiVersion = params.get("apiVersion", None)
        requestedSchemas = params.get("requestedSchemas", None)
        skip = params.get("skip", None)
        limit = params.get("limit", None)
        includeResultsetResponses = params.get("includeResultsetResponses", 'NONE')
        start = params.get("start", None)
        end = params.get("end", None)
        assemblyId = params.get("assemblyId", None)
        referenceName = params.get("referenceName", None)
        referenceBases = params.get("referenceBases", None)
        alternateBases = params.get("alternateBases", None)
        variantMinLength = params.get("variantMinLength", None)
        variantMaxLength = params.get("variantMaxLength", None)
        allele = params.get("allele", None)
        geneid = params.get("geneid", None)
        aminoacidchange = params.get("aminoacidchange", None)
        filters = params.get("filters", None)
        requestedGranularity = query.get("requestedGranularity", "boolean")

    if (event['httpMethod'] == 'POST'):
        params = json.loads(event['body'])
        print(f"POST params {params}")
        meta = params.get("meta", dict())
        query = params.get("query", dict())
        # meta data
        apiVersion = meta.get("apiVersion", None)
        requestedSchemas = meta.get("requestedSchemas", None)
        # query data
        requestParameters = query.get("requestParameters", None)
        requestedGranularity = query.get("requestedGranularity", "boolean")
        # pagination
        pagination = query.get("pagination", dict())
        skip = pagination.get("skip", 0)
        limit = pagination.get("limit", 100)
        currentPage = pagination.get("currentPage", None)
        previousPage = pagination.get("previousPage", None)
        nextPage = pagination.get("nextPage", None)
        # query request params
        requestParameters = query.get("requestParameters", dict())
        # validate query request
        validator = jsonschema.Draft202012Validator(requestSchemaJSON['g_variant'])
        # print(validator.schema)
        if errors := sorted(validator.iter_errors(requestParameters), key=lambda e: e.path):
            return bad_request(errorMessage= "\n".join([error.message for error in errors]))
            # raise error
        start = requestParameters.get("start", None)
        end = requestParameters.get("end", None)
        assemblyId = requestParameters.get("assemblyId", None)
        referenceName = requestParameters.get("referenceName", None)
        referenceBases = requestParameters.get("referenceBases", None)
        alternateBases = requestParameters.get("alternateBases", None)
        variantMinLength = requestParameters.get("variantMinLength", None)
        variantMaxLength = requestParameters.get("variantMaxLength", None)
        allele = requestParameters.get("allele", None)
        geneId = requestParameters.get("geneId", None)
        aminoacidChange = requestParameters.get("aminoacidChange", None)
        filters = requestParameters.get("filters", None)
        variantType = requestParameters.get("variantType", None)
        includeResultsetResponses = requestParameters.get("includeResultsetResponses", 'NONE')

    if event["resource"] == "/g_variants":
        datasets = get_datasets(assemblyId)
        # get vcf file and the name of chromosome in it eg: "chr1", "Chr4", "CHR1" or just "1"
        vcf_chromosomes = get_vcf_chromosome_map(datasets, referenceName)
        if len(start) == 2:
            start_min, start_max = start
        else:
            start_min = start_max = start[0]
        if len(end) == 2:
            end_min, end_max = start
        else:
            end_min = end_max = end[0]
        start_min += 1
        start_max += 1
        end_min += 1
        end_max += 1

        if referenceBases != 'N':
            # For specific reference bases region may be smaller
            max_offset = len(referenceBases) - 1
            end_max = min(start_max + max_offset, end_max)
            start_min = max(end_min - max_offset, start_min)
            if end_min > end_max or start_min > start_max:
                # Region search will find nothing, search a dummy region
                start_min = 2000000000
                start_max = start_min
                end_min = start_min + max_offset
                end_max = end_min
        # threading
        thread_responses = queue.Queue()
        threads = []
        # parallelism across datasets
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
            
            # call split query for each dataset found
            thread = threading.Thread(target=split_query,
                                kwargs={
                                    'dataset_id': dataset_id,
                                    'vcf_locations': vcf_locations,
                                    'vcf_groups': vcf_groups,
                                    'reference_bases': referenceBases,
                                    'region_start': start_min,
                                    'region_end': start_max,
                                    'end_min': end_min,
                                    'end_max': end_max,
                                    'alternate_bases': alternateBases,
                                    'variant_type': variantType,
                                    'include_datasets': includeResultsetResponses,
                                    'requested_granularity': requestedGranularity,
                                    'responses': thread_responses
                                })
            thread.start()
            threads.append(thread)

        num_threads = len(threads)
        processed = 0
        exists = False
        variantCount = 0

        if requestedGranularity == 'boolean':
            while processed < num_threads and (includeResultsetResponses != 'NONE' or not exists):
                thread_response = thread_responses.get()
                processed += 1
                if 'exists' not in thread_response:
                    # function errored out, ignore
                    continue
                exists = exists or thread_response['exists']
    
            response = responses.boolean_response
            response['responseSummary']['exists'] = exists
            print('Returning Response: {}'.format(json.dumps(response)))
            return bundle_response(200, response)

        if requestedGranularity == 'count':
            while processed < num_threads and (includeResultsetResponses != 'NONE' or not exists):
                thread_response = thread_responses.get()
                processed += 1
                if 'exists' not in thread_response:
                    # function errored out, ignore
                    continue
                exists = exists or thread_response['exists']
                variantCount += thread_response.get('variantCount', 0)

            response = responses.counts_response
            response['responseSummary']['exists'] = exists
            response['responseSummary']['numTotalResults'] = variantCount
            print('Returning Response: {}'.format(json.dumps(response)))
            return bundle_response(200, response)

        if requestedGranularity in ('record', 'aggregated'):
            variants = set()
            while processed < num_threads and (includeResultsetResponses != 'NONE' or not exists):
                thread_response = thread_responses.get()
                processed += 1
                if 'exists' not in thread_response:
                    # function errored out, ignore
                    continue
                exists = exists or thread_response['exists']
                variantCount +=  thread_response['variantCount']
                variants.update(thread_response['variants'])

            results = list()
            for variant in variants:
                pos, ref, alt, typ = variant.split('\t')
                results.append(entries.get_variant_entry(variant, assemblyId, ref, alt, int(pos), int(pos) + len(alt), typ))

            response = responses.get_result_sets_response(
                resGranularity='record', 
                setType='genomicVariant', 
                exists=exists,
                total=variantCount,
                results=results
                )
            print('Returning Response: {}'.format(json.dumps(response)))
            return bundle_response(200, response)
    

    elif event['resource'] == '/g_variants/{id}/biosamples':
        entry = responses.result_sets_response
        entry['response']['resultSets'][0]['results'] = [
            entries.biosample_entry]
        response = bundle_response(200, entry)
    else:
        entry = responses.result_sets_response
        entry['response']['resultSets'][0]['results'] = [entries.variant_entry]
        response = bundle_response(200, entry)


if __name__ == '__main__':
    event = {
        "resource": "/g_variants",
        "path": "/g_variants",
        "httpMethod": "POST",
        "body": json.dumps({
            "query": {
                "requestParameters": {
                "assemblyId": "MTD-1",
                "includeResultsetResponses": "HIT",
                "start": [
                    10000000,
                    10001000
                ],
                "end": [
                    10000000,
                    10001000
                ],
                "referenceBases": "A",
                "referenceName": "5",
                "alternateBases": "G"
                }
            }
        })
    }

    print(lambda_handler(event, dict()))