import json

from shared.apiutils import parse_request, bundle_response
from route_phenotypes import route as route_phenotypes

def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))
    request_params, errors, status = parse_request(event)

    if errors:
        return bundle_response(status, errors)

    if event["resource"] == "/phenotypes":
        return route_phenotypes(request_params)

    return bundle_response(
        404,
        {"message": f"Unknown resource {event.get('resource')}"}
    )


if __name__ == "__main__":
    pass
