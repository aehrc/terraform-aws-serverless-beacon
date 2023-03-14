import json
import os
import jsons

from apiutils.api_response import bundle_response
import apiutils.responses as responses
from athena.cohort import Cohort
from athena.common import entity_search_conditions

from athena.filter_functions import new_entity_search_conditions

BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']
COHORTS_TABLE = os.environ['COHORTS_TABLE']
INDIVIDUALS_TABLE = os.environ['INDIVIDUALS_TABLE']
TERMS_INDEX_TABLE = os.environ['TERMS_INDEX_TABLE']
RELATIONS_TABLE = os.environ['RELATIONS_TABLE']


def get_count_query(conditions=[]):
    query = f'''
    SELECT COUNT(id) FROM "{{database}}"."{{table}}"
    {conditions};
    '''
    return query


def get_bool_query(conditions=[]):
    query = f'''
    SELECT 1 FROM "{{database}}"."{{table}}" 
    {conditions}
    LIMIT 1;
    '''
    return query


def get_record_query(skip, limit, conditions=[]):
    query = f'''
    SELECT id, cohortdatatypes, cohortdesign, B.csize as cohortsize, cohorttype, collectionevents, exclusioncriteria, inclusioncriteria, name
    FROM 
        "{{database}}"."{{table}}" as A 
    LEFT JOIN 
        (
            SELECT _cohortid, count(*) as csize 
            FROM "{{database}}"."{INDIVIDUALS_TABLE}"
            GROUP BY _cohortid
        ) as B
    ON A.id = B._cohortid
    {conditions}
    ORDER BY A.id
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

    conditions, execution_parameters = new_entity_search_conditions(filters, 'cohorts', 'cohorts')

    if request.query.requested_granularity =='boolean':
        query = get_bool_query(conditions)
        exists = Cohort.get_existence_by_query(query, execution_parameters=execution_parameters)
        response = responses.get_boolean_response(exists=exists)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity =='count':
        query = get_count_query(conditions)
        count = Cohort.get_count_by_query(query, execution_parameters=execution_parameters)
        response = responses.get_counts_response(exists=count>0, count=count)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == Granularity.RECORD:
        query = get_record_query(skip, limit, conditions)
        cohorts = Cohort.get_by_query(query, execution_parameters=execution_parameters)
        response = responses.get_result_sets_response(
            setType='cohorts', 
            exists=len(cohorts)>0,
            total=len(cohorts),
            reqPagination=responses.get_pagination_object(skip, limit),
            results=jsons.dump(cohorts, strip_privates=True)
        )
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)


if __name__ == '__main__':
    pass
