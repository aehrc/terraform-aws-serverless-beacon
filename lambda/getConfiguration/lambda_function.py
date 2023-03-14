import json

from apiutils.framework import configuration
from apiutils.requests import RequestParams, parse_response
from apiutils.api_response import bundle_response


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    request_params: RequestParams = parse_response(event)
    response = configuration(request_params)
    print('Returning Response: {}'.format(json.dumps(response)))
    return bundle_response(200, response)
