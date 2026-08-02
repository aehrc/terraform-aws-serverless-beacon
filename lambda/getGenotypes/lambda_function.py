import json

from shared.apiutils import parse_request, bundle_response
from route_genotypes import route as route_genotypes

def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))
    request_params, errors, status = parse_request(event)

    if errors:
        return bundle_response(status, errors)

    if event["resource"] == "/genotypes":
        return route_genotypes(request_params)


if __name__ == "__main__":
    pass
