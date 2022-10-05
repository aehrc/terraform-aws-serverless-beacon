import json
import os

from apiutils.api_response import bundle_response
import apiutils.responses as responses


BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']
TERMS_TABLE = os.environ['TERMS_TABLE']
DATASETS_TABLE = os.environ['DATASETS_TABLE']


def route(event):
    print('Event received', event)
    if event['httpMethod'] == 'GET':
        params = event.get('queryStringParameters', None) or dict()
        print(f"Query params {params}")
        apiVersion = params.get("apiVersion", BEACON_API_VERSION)
        requestedSchemas = params.get("requestedSchemas", [])
        skip = params.get("skip", 0)
        limit = params.get("limit", 100)
    if event['httpMethod'] == 'POST':
        params = json.loads(event.get('body') or "{}")
        print(f"POST params {params}")
        meta = params.get("meta", dict())
        query = params.get("query", dict())
        # meta data
        apiVersion = meta.get("apiVersion", BEACON_API_VERSION)
        requestedSchemas = meta.get("requestedSchemas", [])
        # pagination
        pagination = query.get("pagination", dict())
        skip = pagination.get("skip", 0)
        limit = pagination.get("limit", 100)

    exists = False
    response = responses.get_boolean_response(exists=exists, info={ 'message': 'Not implemented' })
    print('Returning Response: {}'.format(json.dumps(response)))
    return bundle_response(200, response)
