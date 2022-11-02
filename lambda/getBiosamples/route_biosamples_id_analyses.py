import json
import os
import jsons

import boto3

from apiutils.api_response import bundle_response
import apiutils.responses as responses
from athena.analysis import Analysis
from dynamodb.ontologies import expand_terms


BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']
INDIVIDUALS_TABLE = os.environ['INDIVIDUALS_TABLE']
ANALYSES_TABLE = os.environ['ANALYSES_TABLE']
TERMS_INDEX_TABLE = os.environ['TERMS_INDEX_TABLE']

s3 = boto3.client('s3')


def get_bool_query(id, conditions=''):
    query = f'''
    SELECT 1 FROM "{{database}}"."{{table}}"
    WHERE "biosampleid"='{id}'
    {'AND ' + conditions if conditions != '' else ''}
    LIMIT 1;
    '''

    return query


def get_count_query(id, conditions=''):
    query = f'''
    SELECT COUNT(*) FROM "{{database}}"."{{table}}"
    WHERE "biosampleid"='{id}'
    {'AND ' + conditions if conditions != '' else ''};
    '''

    return query


def get_record_query(id, skip, limit, conditions=''):
    query = f'''
    SELECT * FROM "{{database}}"."{{table}}"
    WHERE "biosampleid"='{id}'
    {'AND ' + conditions if conditions != '' else ''}
    OFFSET {skip}
    LIMIT {limit};
    '''

    return query


def route(event):
    if event['httpMethod'] == 'GET':
        params = event.get('queryStringParameters', None) or dict()
        print(f"Query params {params}")
        apiVersion = params.get("apiVersion", BEACON_API_VERSION)
        requestedSchemas = params.get("requestedSchemas", [])
        skip = params.get("skip", 0)
        limit = params.get("limit", 100)
        includeResultsetResponses = params.get("includeResultsetResponses", 'NONE')
        filters = [{'id':fil_id} for fil_id in params.get("filters", [])]
        requestedGranularity = params.get("requestedGranularity", "boolean")

    if event['httpMethod'] == 'POST':
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
        filters = query.get("filters", [])
        variantType = requestParameters.get("variantType", None)
        includeResultsetResponses = query.get("includeResultsetResponses", 'NONE')
    
    biosample_id = event["pathParameters"].get("id", None)
    
    conditions = ''
    if len(filters) > 0:
        # supporting ontology terms
        analysis_filters = list(filter(lambda x: x.get('scope', 'analyses') == 'analyses', filters))
        analysis_terms = expand_terms(analysis_filters)
        conditions = f''' id IN (SELECT id FROM {TERMS_INDEX_TABLE} WHERE kind='analyses' AND term IN ({analysis_terms})) '''
    
    if requestedGranularity == 'boolean':
        query = get_bool_query(biosample_id, conditions)
        exists = Analysis.get_existence_by_query(query)
        response = responses.get_boolean_response(exists=exists)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if requestedGranularity == 'count':
        query = get_count_query(biosample_id, conditions)
        count = Analysis.get_count_by_query(query)
        response = responses.get_counts_response(exists=count>0, count=count)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if requestedGranularity in ('record', 'aggregated'):
        query = get_record_query(biosample_id, skip, limit, conditions)
        analyses = Analysis.get_by_query(query)
        response = responses.get_result_sets_response(
            setType='analyses', 
            exists=len(analyses)>0,
            total=len(analyses),
            reqPagination=responses.get_pagination_object(skip, limit),
            results=jsons.dump(analyses, strip_privates=True)
        )
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)
