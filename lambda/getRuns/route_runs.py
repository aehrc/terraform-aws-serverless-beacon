import json
import os
import jsons

from apiutils.api_response import bundle_response
import apiutils.responses as responses
from athena.run import Run
from athena.common import entity_search_conditions

from athena.filter_functions import new_entity_search_conditions

BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']
RUNS_TABLE = os.environ['RUNS_TABLE']
TERMS_INDEX_TABLE = os.environ['TERMS_INDEX_TABLE']


def get_count_query(conditions=''):
    query = f'''
    SELECT COUNT(id) FROM "{{database}}"."{{table}}"
    {conditions}
    '''
    return query


def get_bool_query(conditions=''):
    query = f'''
    SELECT 1 FROM "{{database}}"."{{table}}"
    {conditions}
    LIMIT 1;
    '''
    return query


def get_record_query(skip, limit, conditions=''):
    query = f'''
    SELECT * FROM "{{database}}"."{{table}}"
    {conditions}
    ORDER BY id
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
        filters_list = []
        filters_str = params.get("filters", filters_list)
        if isinstance(filters_str, str):
            filters_list = filters_str.split(',')
        filters = [{'id': fil_id} for fil_id in filters_list]
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

    conditions, execution_parameters = new_entity_search_conditions(filters, 'runs', 'runs')

    if requestedGranularity == 'boolean':
        query = get_bool_query(conditions)
        exists = Run.get_existence_by_query(query, execution_parameters=execution_parameters)
        response = responses.get_boolean_response(exists=exists)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if requestedGranularity == 'count':
        query = get_count_query(conditions)
        count = Run.get_count_by_query(query, execution_parameters=execution_parameters)
        response = responses.get_counts_response(exists=count>0, count=count)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if requestedGranularity in ('record', 'aggregated'):
        query = get_record_query(skip, limit, conditions)
        runs = Run.get_by_query(query, execution_parameters=execution_parameters)
        response = responses.get_result_sets_response(
            setType='runs', 
            exists=len(runs)>0,
            total=len(runs),
            reqPagination=responses.get_pagination_object(skip, limit),
            results=jsons.dump(runs, strip_privates=True)
        )
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)


if __name__ == '__main__':
    pass
