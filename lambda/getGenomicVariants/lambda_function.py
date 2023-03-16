import json

from route_g_variants import route as route_g_variants
from route_g_variants_id import route as route_g_variants_id
from route_g_variants_id_individuals import route as route_g_variants_id_individuals
from route_g_variants_id_biosamples import route as route_g_variants_id_biosamples
from apiutils.requests import RequestParams, parse_request


def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))
    request_params: RequestParams = parse_request(event)

    # if event['httpMethod'] == 'POST':
    #     try:
    #         body_dict = json.loads(event.get('body') or '{}')
    #     except ValueError:
    #         return bad_request(errorMessage='Error parsing request body, Expected JSON.')

    #     validator = Draft202012Validator(schemaRequestBody)
    #     errors = []

    #     for error in sorted(validator.iter_errors(body_dict), key=lambda e: e.path):
    #         error_message = f'{error.message} '
    #         for part in list(error.path):
    #             error_message += f'/{part}'
    #         errors.append(error_message)

    #     if errors:
    #         return bad_request(errorMessage=', '.join(errors))

    # event_hash = hash_query(event)

    if event["resource"] == "/g_variants":
        return route_g_variants(request_params)

    elif event["resource"] == "/g_variants/{id}":
        return route_g_variants_id(
            request_params, event["pathParameters"].get("id", None)
        )

    elif event["resource"] == "/g_variants/{id}/individuals":
        return route_g_variants_id_individuals(
            request_params, event["pathParameters"].get("id", None)
        )

    elif event["resource"] == "/g_variants/{id}/biosamples":
        return route_g_variants_id_biosamples(
            request_params, event["pathParameters"].get("id", None)
        )


if __name__ == "__main__":
    pass
