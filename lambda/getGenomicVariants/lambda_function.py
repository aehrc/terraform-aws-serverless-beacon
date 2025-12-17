import json

from route_g_variants import route as route_g_variants
from route_g_variants_id import route as route_g_variants_id
from route_g_variants_id_individuals import route as route_g_variants_id_individuals
from route_g_variants_id_individuals_s3tables import (
    route as route_g_variants_id_individuals_s3tables,
)
from route_g_variants_id_biosamples import route as route_g_variants_id_biosamples
from shared.apiutils import parse_request, bundle_response


def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))
    request_params, errors, status = parse_request(event)

    if errors:
        return bundle_response(status, errors)

    if event["resource"] == "/g_variants":
        return route_g_variants(request_params)

    elif event["resource"] == "/g_variants/{id}":
        return route_g_variants_id(
            request_params, event["pathParameters"].get("id", None)
        )

    elif event["resource"] == "/g_variants/{id}/individuals":
        query_params = request_params.query.request_parameters

        if not query_params.use_s3_tables:
            return route_g_variants_id_individuals(
                request_params, event["pathParameters"].get("id", None)
            )
        else:
            return route_g_variants_id_individuals_s3tables(
                request_params, event["pathParameters"].get("id", None)
            )

    elif event["resource"] == "/g_variants/{id}/biosamples":
        return route_g_variants_id_biosamples(
            request_params, event["pathParameters"].get("id", None)
        )


if __name__ == "__main__":
    event = {
        "resource": "/g_variants/{id}/individuals",
        "path": "/g_variants/R1JDSDM3CTIyCTE2MDUwOTIyCVQJRw==/individuals",
        "httpMethod": "POST",
        "requestContext": {
            "resourceId": "hyli08",
            "authorizer": {
                "claims": {
                    "cognito:groups": "count-access-user-group,record-access-user-group,boolean-access-user-group,admin-group",
                }
            },
        },
        "queryStringParameters": {"useS3Tables": "true"},
        "pathParameters": {"id": "R1JDSDM3CTIyCTE2MDUwOTIyCVQJRw=="},
        "body": '{"query":{"filters":[],"requestedGranularity":"record","pagination":{"skip":0,"limit":100}},"meta":{"apiVersion":"v2.0"}}',
    }
    event1 = {
        "resource": "/g_variants/{id}/individuals",
        "path": "/g_variants/R1JDSDM3CTIyCTE2MDUwOTIyCVQJRw==/individuals",
        "httpMethod": "POST",
        "requestContext": {
            "resourceId": "hyli08",
            "authorizer": {
                "claims": {
                    "cognito:groups": "count-access-user-group,record-access-user-group,boolean-access-user-group,admin-group",
                }
            },
        },
        "queryStringParameters": {"useS3Tables": "true"},
        "pathParameters": {"id": "R1JDSDM3CTIyCTE2MDUwOTIyCVQJRw=="},
        "body": '{"query":{"filters":[{"scope":"individuals","id":"SNOMED:248153007","includeDescendantTerms":true}],"requestedGranularity":"record","pagination":{"skip":0,"limit":100}},"meta":{"apiVersion":"v2.0"}}',
    }
    # lambda_handler(event, {})
    lambda_handler(event1, {})
