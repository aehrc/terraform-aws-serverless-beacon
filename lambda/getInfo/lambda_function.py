import json
import os
from time import time
from datetime import datetime

from apiutils.responses import build_beacon_info_response
from apiutils.requests import RequestParams, parse_response
from apiutils.api_response import bundle_response


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    request_params: RequestParams = parse_response(event)
    response = build_beacon_info_response([],
                                          request_params,
                                          lambda x, y, z: x,
                                          [])
    print('Returning Response: {}'.format(json.dumps(response)))

    return bundle_response(200, response)
