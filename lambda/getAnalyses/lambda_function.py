import json

from jsonschema import Draft202012Validator

from apiutils.api_response import bad_request
from apiutils.request_hash import hash_query
from route_analyses import route as route_analyses
from route_analyses_filtering_terms import route as route_analyses_filtering_terms
from route_analyses_id import route as route_analyses_id
from route_analyses_id_g_variants import route as route_analyses_id_g_variants


schemaRequestBody = json.load(open('./schemas/requestBody.json'))
schemaVariants = json.load(open('./schemas/gVariantsRequestParameters.json'))


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))

    if event['httpMethod'] == 'POST':
        try:
            body_dict = json.loads(event.get('body') or '{}')
        except ValueError:
            return bad_request(errorMessage='Error parsing request body, Expected JSON.')
        
        if event['resource'] == '/analyses/{id}/g_variants':
            schemaRequestBody['properties']['query']['properties']['requestParameters'] = schemaVariants
        
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

    if event["resource"] == "/analyses":
        return route_analyses(event)

    elif event['resource'] == '/analyses/filtering_terms':
        return route_analyses_filtering_terms(event)

    elif event['resource'] == '/analyses/{id}':
        return route_analyses_id(event)

    elif event['resource'] == '/analyses/{id}/g_variants':
        return route_analyses_id_g_variants(event, event_hash)


if __name__ == '__main__':
    pass
