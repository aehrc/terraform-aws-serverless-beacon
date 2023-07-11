import json

from route_cohorts import route as route_cohorts
from route_cohorts_id import route as route_cohorts_id
from route_cohorts_id_individuals import route as route_cohorts_id_individuals
from route_cohorts_id_filtering_terms import route as route_cohorts_id_filtering_terms
from shared.apiutils import parse_request, bundle_response


def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))
    request_params, errors, status = parse_request(event)

    if errors:
        return bundle_response(status, errors)

    if event["resource"] == "/cohorts":
        return route_cohorts(request_params)

    elif event["resource"] == "/cohorts/{id}":
        return route_cohorts_id(request_params, event["pathParameters"].get("id", None))

    elif event["resource"] == "/cohorts/{id}/individuals":
        return route_cohorts_id_individuals(
            request_params, event["pathParameters"].get("id", None)
        )

    elif event["resource"] == "/cohorts/{id}/filtering_terms":
        return route_cohorts_id_filtering_terms(
            request_params, event["pathParameters"].get("id", None)
        )


if __name__ == "__main__":
    pass
