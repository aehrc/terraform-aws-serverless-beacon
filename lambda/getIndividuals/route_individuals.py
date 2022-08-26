import json
import jsonschema
import os
import jsons

import boto3

from apiutils.api_response import bundle_response, bad_request
import apiutils.responses as responses
from athena.individual import Individual


BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']

s3 = boto3.client('s3')
# requestSchemaJSON = json.load(open("requestParameters.json"))


def get_count_query():
    query = f'''
    SELECT COUNT(*) FROM "{{database}}"."{{table}}";
    '''
    return query


def get_bool_query():
    query = f'''
    SELECT 1 FROM "{{database}}"."{{table}}" LIMIT 1;
    '''
    return query


def get_record_query(skip, limit):
    query = f'''
    SELECT * FROM "{{database}}"."{{table}}"
    OFFSET {skip}
    LIMIT {limit};
    '''
    return query


def route(event):
    if (event['httpMethod'] == 'GET'):
        params = event.get('queryStringParameters', None) or dict()
        print(f"Query params {params}")
        apiVersion = params.get("apiVersion", BEACON_API_VERSION)
        requestedSchemas = params.get("requestedSchemas", [])
        skip = params.get("skip", 0)
        limit = params.get("limit", 100)
        includeResultsetResponses = params.get("includeResultsetResponses", 'NONE')
        filters = params.get("filters", [])
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
        # validator = jsonschema.Draft202012Validator(requestSchemaJSON['g_variant'])
        # print(validator.schema)
        # if errors := sorted(validator.iter_errors(requestParameters), key=lambda e: e.path):
        #     return bad_request(errorMessage= "\n".join([error.message for error in errors]))
            # raise error
        filters = requestParameters.get("filters", [])
        variantType = requestParameters.get("variantType", None)
        includeResultsetResponses = requestParameters.get("includeResultsetResponses", 'NONE')

    if len(filters) > 0:
        # supporting ontology terms
        pass
    
    if requestedGranularity == 'boolean':
        query = get_bool_query()
        exists = Individual.get_existence_by_query(query)
        response = responses.get_boolean_response(exists=exists)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if requestedGranularity == 'count':
        query = get_count_query()
        count = Individual.get_count_by_query(query)
        response = responses.get_counts_response(exists=count>0, count=count)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if requestedGranularity in ('record', 'aggregated'):
        query = get_record_query(skip, limit)
        individuals = Individual.get_by_query(query)
        response = responses.get_result_sets_response(
            setType='individuals', 
            exists=len(individuals)>0,
            total=len(individuals),
            results=jsons.dump(individuals, strip_privates=True)
        )
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)