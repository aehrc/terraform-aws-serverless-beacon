import json

from shared.apiutils import parse_request, bundle_response
from route_individuals import route as route_individuals
from route_individuals_id import route as route_individuals_id
from route_individuals_id_g_variants import route as route_individuals_id_g_variants
from route_individuals_id_biosamples import route as route_individuals_id_biosamples
from route_individuals_filtering_terms import route as route_individuals_filtering_terms


def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))
    request_params, errors, status = parse_request(event)

    if errors:
        return bundle_response(status, errors)

    if event["resource"] == "/individuals":
        return route_individuals(request_params)

    elif event["resource"] == "/individuals/filtering_terms":
        return route_individuals_filtering_terms(request_params)

    elif event["resource"] == "/individuals/{id}":
        return route_individuals_id(
            request_params, event["pathParameters"].get("id", None)
        )

    elif event["resource"] == "/individuals/{id}/g_variants":
        return route_individuals_id_g_variants(
            request_params, event["pathParameters"].get("id", None)
        )

    elif event["resource"] == "/individuals/{id}/biosamples":
        return route_individuals_id_biosamples(
            request_params, event["pathParameters"].get("id", None)
        )


if __name__ == "__main__":
    pass
