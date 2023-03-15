import json
import jsons

import boto3

from apiutils.api_response import bundle_response
import apiutils.responses as responses
from athena.biosample import Biosample
from apiutils.schemas import DefaultSchemas
from apiutils.requests import RequestParams, Granularity


s3 = boto3.client('s3')


def get_record_query(id):
    query = f'''
    SELECT * FROM "{{database}}"."{{table}}"
    WHERE "id"='{id}'
    LIMIT 1;
    '''

    return query


def route(request: RequestParams, biosample_id):
    if request.query.requested_granularity == Granularity.BOOLEAN:
        query = get_record_query(biosample_id)
        count = 1 if Biosample.get_existence_by_query(query) else 0
        response = responses.build_beacon_boolean_response(
            {}, count, request, {}, DefaultSchemas.BIOSAMPLES)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == Granularity.COUNT:
        query = get_record_query(biosample_id)
        count = 1 if Biosample.get_existence_by_query(query) else 0
        response = responses.build_beacon_count_response(
            {}, count, request, {}, DefaultSchemas.BIOSAMPLES)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == Granularity.RECORD:
        query = get_record_query(biosample_id)
        biosamples = Biosample.get_by_query(query)
        response = responses.build_beacon_resultset_response(
            jsons.dump(biosamples, strip_privates=True), len(biosamples), request, {}, DefaultSchemas.BIOSAMPLES)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)
