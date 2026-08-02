import json

from shared.apiutils import parse_request, bundle_response
from route_snps import route as route_snps

def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))
    request_params, errors, status = parse_request(event)

    if errors:
        return bundle_response(status, errors)

    if event["resource"] == "/snps":
        return route_snps(request_params)


if __name__ == "__main__":
    pass
