import json
import os
import jsons

import boto3

from apiutils.api_response import bundle_response
import apiutils.responses as responses
from athena.individual import Individual
from dynamodb.onto_index import OntoData


BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']
INDIVIDUALS_TABLE = os.environ['INDIVIDUALS_TABLE']
ANALYSES_TABLE = os.environ['ANALYSES_TABLE']

s3 = boto3.client('s3')


def get_bool_query(id, conditions=[]):
    query = f'''
    SELECT 1 FROM "{{database}}"."{{table}}"
    WHERE "_datasetid"='{id}'
    {('AND ' if len(conditions) > 0 else '') + ' AND '.join(conditions)}
    LIMIT 1;
    '''

    return query


def get_count_query(id, conditions=[]):
    query = f'''
    SELECT COUNT(*) FROM "{{database}}"."{{table}}"
    WHERE "_datasetid"='{id}'
    {('AND ' if len(conditions) > 0 else '') + ' AND '.join(conditions)};
    '''

    return query


def get_record_query(id, skip, limit, conditions=[]):
    query = f'''
    SELECT * FROM "{{database}}"."{{table}}"
    WHERE "_datasetid"='{id}'
    {('AND ' if len(conditions) > 0 else '') + ' AND '.join(conditions)}
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
        filters = requestParameters.get("filters", [])
        variantType = requestParameters.get("variantType", None)
        includeResultsetResponses = query.get("includeResultsetResponses", 'NONE')
    
    dataset_id = event["pathParameters"].get("id", None)
    
    # by default the scope of terms is assumed to be individuals
    terms_found = True
    individuals_term_columns = []
    # TODO
    # individuals_term_columns = []
    sql_conditions = []
    
    if len(filters) > 0:
        for fil in filters:
            if fil.get('scope', 'individuals') == 'individuals':
                terms_found = False
                for item in OntoData.tableTermsIndex.query(hash_key=f'{ANALYSES_TABLE}\t{fil["id"]}'):
                    individuals_term_columns.append((item.term, item.columnName))
                    terms_found = True
    
        # for fil in filters:
        #     if fil.get('scope') == 'individuals':
        #         terms_found = False
        #         for item in OntoData.tableTermsIndex.query(hash_key=f'{INDIVIDUALS_TABLE}\t{fil["id"]}'):
        #             individuals_term_columns.append((item.term, item.columnName))
        #             terms_found = True

    if not terms_found:
        response = responses.get_boolean_response(exists=False)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    for term, col in individuals_term_columns:
        cond = f'''
            JSON_EXTRACT_SCALAR("{ANALYSES_TABLE}"."{col}", '$.id')='{term}' 
        '''
        sql_conditions.append(cond)

    # for term, col in individuals_term_columns:
    #     cond = f'''
    #         JSON_EXTRACT_SCALAR("{INDIVIDUALS_TABLE}"."{col}", '$.id')='{term}' 
    #     '''
    #     sql_conditions.append(cond)
    
    if requestedGranularity == 'boolean':
        query = get_bool_query(dataset_id)
        exists = Individual.get_existence_by_query(query)
        response = responses.get_boolean_response(exists=exists)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if requestedGranularity == 'count':
        query = get_count_query(dataset_id)
        count = Individual.get_count_by_query(query)
        response = responses.get_counts_response(exists=count>0, count=count)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if requestedGranularity in ('record', 'aggregated'):
        query = get_record_query(dataset_id, skip, limit)
        individuals = Individual.get_by_query(query)
        response = responses.get_result_sets_response(
            setType='individuals', 
            exists=len(individuals)>0,
            total=len(individuals),
            reqPagination=responses.get_pagination_object(skip, limit),
            results=jsons.dump(individuals, strip_privates=True)
        )
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)
