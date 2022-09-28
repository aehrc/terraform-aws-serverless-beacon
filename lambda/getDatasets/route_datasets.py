import json
import os
import jsons

from apiutils.api_response import bundle_response
import apiutils.responses as responses
from athena.dataset import Dataset
from dynamodb.onto_index import OntoData


BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']
DATASETS_TABLE = os.environ['DATASETS_TABLE']


def get_count_query(conditions=[]):
    query = f'''
    SELECT COUNT(id) FROM "{{database}}"."{{table}}"
    {('WHERE ' if len(conditions) > 0 else '') + ' AND '.join(conditions)};
    '''
    return query


def get_bool_query(conditions=[]):
    query = f'''
    SELECT 1 FROM "{{database}}"."{{table}}" LIMIT 1
    {('WHERE ' if len(conditions) > 0 else '') + ' AND '.join(conditions)};
    '''
    return query


def get_record_query(skip, limit, conditions=[]):
    query = f'''
    SELECT * FROM "{{database}}"."{{table}}"
    {('WHERE ' if len(conditions) > 0 else '') + ' AND '.join(conditions)}
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
        filters = query.get("filters", [])
        # query request params
        requestParameters = query.get("requestParameters", dict())
        includeResultsetResponses = query.get("includeResultsetResponses", 'NONE')

    # scope = datasets
    terms_found = True
    term_columns = []
    sql_conditions = []

    if len(filters) > 0:
        # supporting ontology terms
        for fil in filters:
            terms_found = False
            for item in OntoData.tableTermsIndex.query(hash_key=f'{DATASETS_TABLE}\t{fil["id"]}'):
                term_columns.append((item.term, item.columnName))
                terms_found = True
   
    for term, col in term_columns:
        cond = f'''
            JSON_EXTRACT_SCALAR("{col}", '$.id')='{term}' 
        '''
        sql_conditions.append(cond)

    if not terms_found:
        response = responses.get_boolean_response(exists=False)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if requestedGranularity == 'boolean':
        query = get_bool_query(sql_conditions)
        exists = Dataset.get_existence_by_query(query)
        response = responses.get_boolean_response(exists=exists)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if requestedGranularity == 'count':
        query = get_count_query(sql_conditions)
        count = Dataset.get_count_by_query(query)
        response = responses.get_counts_response(exists=count>0, count=count)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if requestedGranularity in ('record', 'aggregated'):
        query = get_record_query(skip, limit, sql_conditions)
        datasets = Dataset.get_by_query(query)
        response = responses.get_result_sets_response(
            setType='datasets', 
            exists=len(datasets)>0,
            total=len(datasets),
            reqPagination=responses.get_pagination_object(skip, limit),
            results=jsons.dump(datasets, strip_privates=True)
        )
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)


if __name__ == '__main__':
    pass
