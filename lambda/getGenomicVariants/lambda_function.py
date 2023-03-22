import json

from jsonschema import Draft202012Validator

from apiutils.api_response import bad_request
from apiutils.request_hash import hash_query
from route_g_variants import route as route_g_variants
from route_g_variants_id import route as route_g_variants_id
from route_g_variants_id_individuals import route as route_g_variants_id_individuals
from route_g_variants_id_biosamples import route as route_g_variants_id_biosamples


schemaRequestBody = json.load(open('./schemas/requestBody.json'))
schemaVariants = json.load(open('./schemas/gVariantsRequestParameters.json'))
schemaRequestBody['properties']['query']['properties']['requestParameters'] = schemaVariants


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))

    if event['httpMethod'] == 'POST':
        try:
            body_dict = json.loads(event.get('body') or '{}')
        except ValueError:
            return bad_request(errorMessage='Error parsing request body, Expected JSON.')

        validator = Draft202012Validator(schemaRequestBody)
        errors = []
        
        for error in sorted(validator.iter_errors(body_dict), key=lambda e: e.path):
            error_message = f'{error.message} '
            for part in list(error.path):
                error_message += f'/{part}'
            errors.append(error_message)

        if errors:
            return bad_request(errorMessage=', '.join(errors))

    event_hash = hash_query(event)

    if event["resource"] == "/g_variants":
        return route_g_variants(event, event_hash)

    elif event['resource'] == '/g_variants/{id}':
        return route_g_variants_id(event, event_hash)

    elif event['resource'] == '/g_variants/{id}/individuals':
        return route_g_variants_id_individuals(event, event_hash)

    elif event['resource'] == '/g_variants/{id}/biosamples':
        return route_g_variants_id_biosamples(event, event_hash)


if __name__ == '__main__':
    pass
