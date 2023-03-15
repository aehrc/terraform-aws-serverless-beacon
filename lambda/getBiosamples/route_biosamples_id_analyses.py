import json

import jsons
import boto3

from apiutils.api_response import bundle_response
from athena.filter_functions import new_entity_search_conditions
import apiutils.responses as responses
from athena.analysis import Analysis
from apiutils.schemas import DefaultSchemas
from apiutils.requests import RequestParams, Granularity


s3 = boto3.client('s3')


def get_bool_query(id, conditions=''):
    query = f'''
    SELECT 1 FROM "{{database}}"."{{table}}"
    WHERE "biosampleid"='{id}'
    {('AND ' + conditions) if len(conditions) > 0 else ''}
    LIMIT 1;
    '''

    return query


def get_count_query(id, conditions=''):
    query = f'''
    SELECT COUNT(*) FROM "{{database}}"."{{table}}"
    WHERE "biosampleid"='{id}'
    {('AND ' + conditions) if len(conditions) > 0 else ''}
    '''

    return query


def get_record_query(id, skip, limit, conditions=''):
    query = f'''
    SELECT * FROM "{{database}}"."{{table}}"
    WHERE "biosampleid"='{id}'
    {('AND ' + conditions) if len(conditions) > 0 else ''}
    ORDER BY id
    OFFSET {skip}
    LIMIT {limit};
    '''

    return query


def route(request: RequestParams, biosample_id):
    conditions, execution_parameters = new_entity_search_conditions(
        request.query.filters, 'analyses', 'biosamples', with_where=False)

    if request.query.requested_granularity == Granularity.BOOLEAN:
        query = get_bool_query(biosample_id, conditions)
        count = 1 if Analysis.get_existence_by_query(
            query, execution_parameters=execution_parameters) else 0
        response = responses.build_beacon_boolean_response(
            {}, count, request, {}, DefaultSchemas.ANALYSES)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == Granularity.COUNT:
        query = get_count_query(biosample_id, conditions)
        count = Analysis.get_count_by_query(
            query, execution_parameters=execution_parameters)
        response = responses.build_beacon_count_response(
            {}, count, request, {}, DefaultSchemas.ANALYSES)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == Granularity.RECORD:
        query = get_record_query(
            biosample_id, request.query.pagination.skip, request.query.pagination.limit, conditions)
        analyses = Analysis.get_by_query(
            query, execution_parameters=execution_parameters)
        response = responses.build_beacon_resultset_response(
            jsons.dump(analyses, strip_privates=True), len(analyses), request, {}, DefaultSchemas.ANALYSES)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)
