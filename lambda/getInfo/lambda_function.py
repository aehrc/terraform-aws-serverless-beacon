import json

from shared.apiutils import (
    RequestParams,
    parse_request,
    build_beacon_info_response,
    bundle_response,
)


def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))
    request_params: RequestParams = parse_request(event)
    authorised_datasets = []
    response = build_beacon_info_response(authorised_datasets, request_params)
    print("Returning Response: {}".format(json.dumps(response)))
    return bundle_response(200, response)
