import json
import os

from api_response import bundle_response
import responses

BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']

def get_analyses(event):
    print(event)
    response = responses.result_sets_response
    # response = responses.counts_response
    # response = responses.boolean_response

    return bundle_response(200, response)


def lambda_handler(event, context):
    if (event['requestContext'] == 'GET'):
        apiVersion = event['queryStringParameters'].get("apiVersion", None)
        requestedSchemas = event['queryStringParameters'].get("requestedSchemas", None)
        pagination = event['queryStringParameters'].get("pagination", None)
        requestedGranularity = event['queryStringParameters'].get("requestedGranularity", None)
    if (event['requestContext'] == 'POST'):
        apiVersion = event['body'].get("apiVersion", None)
        requestedSchemas = event['body'].get("requestedSchemas", None)
        pagination = event['body'].get("pagination", None)
        requestedGranularity = event['body'].get("requestedGranularity", None)

    print('Event Received: {}'.format(json.dumps(event)))
    if event['resource'] == '/analyses/{id}/g_variants':
        response = bundle_response(200, responses.g_variants_response)
    else:
        response = get_analyses(event)
    print('Returning Response: {}'.format(json.dumps(response)))
    return response