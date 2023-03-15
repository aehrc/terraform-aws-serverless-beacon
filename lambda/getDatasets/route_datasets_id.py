import json
import os

import jsons


import apiutils.responses as responses
from athena.dataset import Dataset
from apiutils.schemas import DefaultSchemas
from apiutils.requests import RequestParams, Granularity


BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']


def get_record_query(id):
    query = f'''
    SELECT * FROM "{{database}}"."{{table}}"
    WHERE "id"='{id}'
    LIMIT 1;
    '''

    return query


def route(request: RequestParams, dataset_id):
    if request.query.requested_granularity == Granularity.BOOLEAN:
        query = get_record_query(dataset_id)
        count = 1 if Dataset.get_existence_by_query(query) else 0
        response = responses.build_beacon_boolean_response(
            {}, count, request, {}, DefaultSchemas.DATASETS)
        print('Returning Response: {}'.format(json.dumps(response)))
        return responses.bundle_response(200, response)

    if request.query.requested_granularity == Granularity.COUNT:
        query = get_record_query(dataset_id)
        count = 1 if Dataset.get_existence_by_query(query) else 0
        response = responses.build_beacon_count_response(
            {}, count, request, {}, DefaultSchemas.DATASETS)
        print('Returning Response: {}'.format(json.dumps(response)))
        return responses.bundle_response(200, response)

    if request.query.requested_granularity == Granularity.RECORD:
        query = get_record_query(dataset_id)
        datasets = Dataset.get_by_query(query)
        response = responses.build_beacon_collection_response(
            jsons.dump(datasets, strip_privates=True), len(datasets), request, lambda x, y: x, DefaultSchemas.DATASETS)
        print('Returning Response: {}'.format(json.dumps(response)))
        return responses.bundle_response(200, response)
