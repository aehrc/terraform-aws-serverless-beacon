from collections import defaultdict
import json
import jsonschema
import queue
import threading
import boto3
import os
import base64
import jsons


from apiutils.api_response import bundle_response, bad_request
from variantutils.search_variants import perform_variant_search
from dynamodb.datasets import Dataset
import apiutils.responses as responses
from athena.biosample import Biosample

SPLIT_SIZE = 1000000
BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']
SPLIT_QUERY = os.environ['SPLIT_QUERY_LAMBDA']
ATHENA_WORKGROUP = os.environ['ATHENA_WORKGROUP']
METADATA_DATABASE = os.environ['METADATA_DATABASE']
INDIVIDUALS_TABLE = os.environ['INDIVIDUALS_TABLE']
BIOSAMPLES_TABLE = os.environ['BIOSAMPLES_TABLE']

dynamodb = boto3.client('dynamodb')
aws_lambda = boto3.client('lambda')
athena = boto3.client('athena')
s3 = boto3.client('s3')
requestSchemaJSON = json.load(open("requestParameters.json"))


# TODO break into many queries (ATHENA SQL LIMIT)
# https://docs.aws.amazon.com/athena/latest/ug/service-limits.html
def get_queries(datasetId, sampleNames):
    query = f'''
    SELECT "{METADATA_DATABASE}"."{BIOSAMPLES_TABLE}".* 
    FROM "{METADATA_DATABASE}"."{INDIVIDUALS_TABLE}" JOIN "{METADATA_DATABASE}"."{BIOSAMPLES_TABLE}" 
    ON 
        "{METADATA_DATABASE}"."{INDIVIDUALS_TABLE}".id
        =
        "{METADATA_DATABASE}"."{BIOSAMPLES_TABLE}".individualid
    WHERE 
        "{METADATA_DATABASE}"."{INDIVIDUALS_TABLE}".datasetid='{datasetId}'
        AND 
        "{METADATA_DATABASE}"."{BIOSAMPLES_TABLE}".datasetid='{datasetId}'
        AND
            "{METADATA_DATABASE}"."{INDIVIDUALS_TABLE}"."samplename" 
        IN ({','.join([f"'{sn}'" for sn in sampleNames])});
    '''
    return query


def get_datasets(assembly_id, dataset_ids=None):
    items = []
    for item in Dataset.datasetIndex.query(assembly_id):
        items.append(item)
    # TODO support more advanced querying
    if dataset_ids:
        items = [i for i in items if i.id in dataset_ids]
    return items


def route(event):
    if (event['httpMethod'] == 'GET'):
        params = event.get('queryStringParameters', dict()) or dict()
        print(f"Query params {params}")
        apiVersion = params.get("apiVersion", BEACON_API_VERSION)
        requestedSchemas = params.get("requestedSchemas", [])
        requestedGranularity = params.get("requestedGranularity", "boolean")

    if (event['httpMethod'] == 'POST'):
        params = json.loads(event.get('body', "{}")) or dict()
        print(f"POST params {params}")
        meta = params.get("meta", dict())
        query = params.get("query", dict())
        # meta data
        apiVersion = meta.get("apiVersion", BEACON_API_VERSION)
        requestedSchemas = meta.get("requestedSchemas", [])
        # query data
        requestedGranularity = query.get("requestedGranularity", "boolean")
        requestParameters = query.get("requestParameters", dict())
        # validate query request
        validator = jsonschema.Draft202012Validator(requestSchemaJSON['g_variant'])
        # print(validator.schema)
        if errors := sorted(validator.iter_errors(requestParameters), key=lambda e: e.path):
            return bad_request(errorMessage= "\n".join([error.message for error in errors]))
            # raise error

    variant_id = event["pathParameters"].get("id", None)
    if variant_id is None:
        return bad_request(errorMessage="Request missing variant ID")
    
    dataset_hash = base64.b64decode(variant_id.encode()).decode()
    assemblyId, referenceName, pos, referenceBases, alternateBases = dataset_hash.split('\t')
    pos = int(pos) - 1
    start = [pos, pos + len(alternateBases)]
    end = [pos, pos + len(alternateBases)]
    datasets = get_datasets(assemblyId)
    includeResultsetResponses = 'ALL'

    exists, query_responses = perform_variant_search(
        passthrough={
            'samplesOnly': True
        },
        datasets=datasets,
        referenceName=referenceName,
        referenceBases=referenceBases,
        alternateBases=alternateBases,
        start=start,
        end=end,
        variantType=None,
        variantMinLength=0,
        variantMaxLength=-1,
        requestedGranularity=requestedGranularity,
        includeResultsetResponses=includeResultsetResponses
    )
    
    dataset_samples = defaultdict(set)
    count = 0

    for query_response in query_responses:
        # immediately return the boolean response if exists
        if requestedGranularity == 'boolean' and exists:
            response = responses.get_boolean_response(exists=exists)
            response['responseSummary']['exists'] = exists
            print('Returning Response: {}'.format(json.dumps(response)))
            return bundle_response(200, response)
        else:
            exists = exists or query_response.exists
            if exists:
                exists = True
                dataset_samples[query_response.dataset_id].update(query_response.sample_names)
                count += query_response.call_count

    if requestedGranularity == 'boolean':
        # TODO biosamples table access
        response = responses.get_boolean_response(exists=exists)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if requestedGranularity == 'count':
        # TODO biosamples table access
        response = responses.get_counts_response(exists=exists, count=count)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if requestedGranularity in ('record', 'aggregated'):
        biosamples = queue.Queue()
        threads = []
        for dataset_id, sample_names in dataset_samples.items():
            if (len(sample_names)) > 0:
                thread = threading.Thread(
                    target=Biosample.get_by_query,
                    kwargs={ 
                        'query': get_queries(dataset_id, sample_names),
                        'queue': biosamples
                    }
                )
                thread.start()
                threads.append(thread)
        
        [thread.join() for thread in threads]
        biosamples = list(biosamples.queue)

        response = responses.get_result_sets_response(
            setType='biosample', 
            exists=exists,
            total=count,
            results=jsons.dump(biosamples, strip_privates=True)
        )
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)


if __name__ == '__main__':
    pass
