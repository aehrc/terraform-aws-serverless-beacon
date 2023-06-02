import json

from route_biosamples import route as route_biosamples
from route_biosamples_id import route as route_biosamples_id
from route_biosamples_id_g_variants import route as route_biosamples_id_g_variants
from route_biosamples_id_analyses import route as route_biosamples_id_analyses
from route_biosamples_id_runs import route as route_biosamples_id_runs
from route_biosamples_filtering_terms import route as route_biosamples_filtering_terms
from shared.apiutils import parse_request, bundle_response


def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))
    request_params, errors, status = parse_request(event)
    
    if errors:
        return bundle_response(status, errors)

    if event["resource"] == "/biosamples":
        return route_biosamples(request_params)

    elif event["resource"] == "/biosamples/{id}":
        return route_biosamples_id(
            request_params, event["pathParameters"].get("id", None)
        )

    elif event["resource"] == "/biosamples/{id}/g_variants":
        return route_biosamples_id_g_variants(
            request_params, event["pathParameters"].get("id", None)
        )

    elif event["resource"] == "/biosamples/{id}/analyses":
        return route_biosamples_id_analyses(
            request_params, event["pathParameters"].get("id", None)
        )

    elif event["resource"] == "/biosamples/{id}/runs":
        return route_biosamples_id_runs(
            request_params, event["pathParameters"].get("id", None)
        )

    elif event["resource"] == "/biosamples/filtering_terms":
        return route_biosamples_filtering_terms(request_params)


if __name__ == "__main__":
    pass
