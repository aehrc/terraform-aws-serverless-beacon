import json
import jsonschema
import os
import jsons

import boto3

from apiutils.api_response import bundle_response, bad_request
import apiutils.responses as responses
from athena.run import Run


BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']

s3 = boto3.client('s3')
# requestSchemaJSON = json.load(open("requestParameters.json"))


def get_record_query(id):
    query = f'''
    SELECT * FROM "{{database}}"."{{table}}"
    WHERE "id"='{id}';
    '''

    return query


def route(event):
    if (event['httpMethod'] == 'GET'):
        params = event.get('queryStringParameters', None) or dict()
        print(f"Query params {params}")
        apiVersion = params.get("apiVersion", BEACON_API_VERSION)
        requestedSchemas = params.get("requestedSchemas", [])
        requestedGranularity = params.get("requestedGranularity", "boolean")

    if (event['httpMethod'] == 'POST'):
        params = json.loads(event.get('body') or "{}")
        print(f"POST params {params}")
        meta = params.get("meta", dict())
        query = params.get("query", dict())
        # meta data
        apiVersion = meta.get("apiVersion", BEACON_API_VERSION)
        requestedSchemas = meta.get("requestedSchemas", [])
        # query data
        requestedGranularity = query.get("requestedGranularity", "boolean")
        # query request params
        requestParameters = query.get("requestParameters", dict())
        # validate query request
        # validator = jsonschema.Draft202012Validator(requestSchemaJSON['g_variant'])
        # print(validator.schema)
        # if errors := sorted(validator.iter_errors(requestParameters), key=lambda e: e.path):
        #     return bad_request(errorMessage= "\n".join([error.message for error in errors]))
            # raise error
    
    run_id = event["pathParameters"].get("id", None)
    
    if requestedGranularity == 'boolean':
        query = get_record_query(run_id)
        exists = Run.get_existence_by_query(query)
        response = responses.get_boolean_response(exists=exists)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if requestedGranularity == 'count':
        query = get_record_query(run_id)
        count = Run.get_count_by_query(query)
        response = responses.get_counts_response(exists=count>0, count=count)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if requestedGranularity in ('record', 'aggregated'):
        query = get_record_query(run_id)
        runs = Run.get_by_query(query)
        response = responses.get_result_sets_response(
            setType='runs', 
            exists=len(runs)>0,
            total=len(runs),
            results=jsons.dump(runs, strip_privates=True)
        )
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)
