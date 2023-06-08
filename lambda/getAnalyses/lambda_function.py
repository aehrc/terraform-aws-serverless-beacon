import json

from route_analyses import route as route_analyses
from route_analyses_filtering_terms import route as route_analyses_filtering_terms
from route_analyses_id import route as route_analyses_id
from route_analyses_id_g_variants import route as route_analyses_id_g_variants
from shared.apiutils import parse_request, bundle_response


def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))
    request_params, errors, status = parse_request(event)
    
    if errors:
        return bundle_response(status, errors)

    if event["resource"] == "/analyses":
        return route_analyses(request_params)

    elif event["resource"] == "/analyses/filtering_terms":
        return route_analyses_filtering_terms(request_params)

    elif event["resource"] == "/analyses/{id}":
        return route_analyses_id(
            request_params, event["pathParameters"].get("id", None)
        )

    elif event["resource"] == "/analyses/{id}/g_variants":
        return route_analyses_id_g_variants(
            request_params, event["pathParameters"].get("id", None)
        )


if __name__ == "__main__":
    pass
