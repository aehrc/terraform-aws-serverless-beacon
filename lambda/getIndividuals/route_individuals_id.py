import json
import jsons

from apiutils.api_response import bundle_response
import apiutils.responses as responses
from athena.individual import Individual
from apiutils.schemas import DefaultSchemas
from apiutils.requests import RequestParams, Granularity


def get_record_query(id):
    query = f'''
    SELECT * FROM "{{database}}"."{{table}}"
    WHERE "id"='{id}'
    LIMIT 1;
    '''

    return query


def route(request: RequestParams, individual_id):
    if request.query.requested_granularity == 'boolean':
        query = get_record_query(individual_id)
        count = 1 if Individual.get_existence_by_query(query) else 0
        response = responses.build_beacon_boolean_response(
            {}, count, request, {}, DefaultSchemas.INDIVIDUALS)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == 'count':
        query = get_record_query(individual_id)
        count = 1 if Individual.get_existence_by_query(query) else 0
        response = responses.build_beacon_count_response(
            {}, count, request, {}, DefaultSchemas.INDIVIDUALS)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == Granularity.RECORD:
        query = get_record_query(individual_id)
        individuals = Individual.get_by_query(query)
        response = responses.build_beacon_resultset_response(
            jsons.dump(individuals, strip_privates=True), len(individuals), request, {}, DefaultSchemas.INDIVIDUALS)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)
