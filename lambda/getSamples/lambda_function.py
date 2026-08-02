import json

from shared.apiutils import parse_request, bundle_response
from route_samples import route as route_samples

def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))
    request_params, errors, status = parse_request(event)

    if errors:
        return bundle_response(status, errors)

    if event["resource"] == "/samples":
        return route_samples(request_params)


if __name__ == "__main__":
    pass
