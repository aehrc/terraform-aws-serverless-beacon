import json

from route_analyses import route as route_analyses
from route_analyses_filtering_terms import route as route_analyses_filtering_terms
from route_analyses_id import route as route_analyses_id
from route_analyses_id_g_variants import route as route_analyses_id_g_variants
from shared.apiutils.requests import RequestParams, parse_request


def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))
    request_params: RequestParams = parse_request(event)

    # if event['httpMethod'] == 'POST':
    #     try:
    #         body_dict = json.loads(event.get('body') or '{}')
    #     except ValueError:
    #         return bad_request(errorMessage='Error parsing request body, Expected JSON.')

    #     if event['resource'] == '/analyses/{id}/g_variants':
    #         schemaRequestBody['properties']['query']['properties']['requestParameters'] = schemaVariants

    #     validator = Draft202012Validator(schemaRequestBody)
    #     errors = []

    #     for error in sorted(validator.iter_errors(body_dict), key=lambda e: e.path):
    #         error_message = f'{error.message} '
    #         for part in list(error.path):
    #             error_message += f'/{part}'
    #         errors.append(error_message)

    #     if errors:
    #         return bad_request(errorMessage=', '.join(errors))

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
