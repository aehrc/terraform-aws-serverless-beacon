import json

from route_runs import route as route_runs
from route_runs_id import route as route_runs_id
from route_runs_id_g_variants import route as route_runs_id_g_variants
from route_runs_id_analyses import route as route_runs_id_analyses
from route_runs_filtering_terms import route as route_runs_filtering_terms
from shared.apiutils import parse_request, bundle_response


def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))
    request_params, errors, status = parse_request(event)
    
    if errors:
        return bundle_response(status, errors)

    if event["resource"] == "/runs":
        return route_runs(request_params)

    elif event["resource"] == "/runs/{id}":
        return route_runs_id(request_params, event["pathParameters"].get("id", None))

    elif event["resource"] == "/runs/{id}/g_variants":
        return route_runs_id_g_variants(
            request_params, event["pathParameters"].get("id", None)
        )

    elif event["resource"] == "/runs/{id}/analyses":
        return route_runs_id_analyses(
            request_params, event["pathParameters"].get("id", None)
        )

    elif event["resource"] == "/runs/filtering_terms":
        return route_runs_filtering_terms(request_params)


if __name__ == "__main__":
    pass
