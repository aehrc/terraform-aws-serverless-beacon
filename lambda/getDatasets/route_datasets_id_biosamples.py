import json
import jsons


from athena.filter_functions import entity_search_conditions
from apiutils.requests import RequestParams, Granularity
from apiutils.schemas import DefaultSchemas
import apiutils.responses as responses
from athena.biosample import Biosample


def get_bool_query(id, conditions=''):
    query = f'''
    SELECT 1 FROM "{{database}}"."{{table}}"
    WHERE "_datasetid"='{id}'
    {('AND ' + conditions) if len(conditions) > 0 else ''}
    LIMIT 1;
    '''

    return query


def get_count_query(id, conditions=''):
    query = f'''
    SELECT COUNT(*) FROM "{{database}}"."{{table}}"
    WHERE "_datasetid"='{id}'
    {('AND ' + conditions) if len(conditions) > 0 else ''}
    '''

    return query


def get_record_query(id, skip, limit, conditions=''):
    query = f'''
    SELECT * FROM "{{database}}"."{{table}}"
    WHERE "_datasetid"='{id}'
    {('AND ' + conditions) if len(conditions) > 0 else ''}
    ORDER BY id
    OFFSET {skip}
    LIMIT {limit};
    '''

    return query


def route(request: RequestParams, dataset_id):
    conditions, execution_parameters = entity_search_conditions(
        request.query.filters, 'biosamples', 'biosamples', with_where=False)

    if request.query.requested_granularity == 'boolean':
        query = get_bool_query(dataset_id, conditions)
        count = 1 if Biosample.get_existence_by_query(
            query, execution_parameters=execution_parameters) else 0
        response = responses.build_beacon_boolean_response(
            {}, count, request, {}, DefaultSchemas.BIOSAMPLES)
        print('Returning Response: {}'.format(json.dumps(response)))
        return responses.bundle_response(200, response)

    if request.query.requested_granularity == 'count':
        query = get_count_query(dataset_id, conditions)
        count = Biosample.get_count_by_query(
            query, execution_parameters=execution_parameters)
        response = responses.build_beacon_count_response(
            {}, count, request, {}, DefaultSchemas.BIOSAMPLES)
        print('Returning Response: {}'.format(json.dumps(response)))
        return responses.bundle_response(200, response)

    if request.query.requested_granularity == Granularity.RECORD:
        query = get_record_query(
            dataset_id, request.query.pagination.skip, request.query.pagination.limit, conditions)
        biosamples = Biosample.get_by_query(
            query, execution_parameters=execution_parameters)
        response = responses.build_beacon_resultset_response(
            jsons.dump(biosamples, strip_privates=True), len(biosamples), request, {}, DefaultSchemas.BIOSAMPLES)
        print('Returning Response: {}'.format(json.dumps(response)))
        return responses.bundle_response(200, response)
