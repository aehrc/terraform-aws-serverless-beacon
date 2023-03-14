import json
import jsons

from apiutils.api_response import bundle_response
from apiutils.requests import RequestParams, Granularity
from apiutils.schemas import DefaultSchemas
import apiutils.responses as responses
from athena.biosample import Biosample
from athena.filter_functions import new_entity_search_conditions


def get_count_query(conditions=''):
    query = f'''
    SELECT COUNT(id) FROM "{{database}}"."{{table}}"
    {conditions};
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


def route(request: RequestParams):
    conditions, execution_parameters = new_entity_search_conditions(
        request.query.filters, 'biosamples', 'biosamples')

    if request.query.requested_granularity == Granularity.BOOLEAN:
        query = get_bool_query(conditions)
        count = 1 if Biosample.get_existence_by_query(
            query, execution_parameters=execution_parameters) else 0
        response = responses.build_beacon_boolean_response(
            {}, count, request, {}, DefaultSchemas.BIOSAMPLES)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == Granularity.COUNT:
        query = get_count_query(conditions)
        count = Biosample.get_count_by_query(
            query, execution_parameters=execution_parameters)
        response = responses.build_beacon_count_response(
            {}, count, request, {}, DefaultSchemas.BIOSAMPLES)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == Granularity.RECORD:
        query = get_record_query(
            request.query.pagination.skip, request.query.pagination.limit, conditions)
        biosamples = Biosample.get_by_query(
            query, execution_parameters=execution_parameters)
        response = responses.build_beacon_resultset_response(
            jsons.dump(biosamples, strip_privates=True), len(biosamples), request, {}, DefaultSchemas.BIOSAMPLES)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)


if __name__ == '__main__':
    pass
