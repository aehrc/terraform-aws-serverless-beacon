import json

from jsonschema import Draft202012Validator

from apiutils.api_response import bad_request
from route_cohorts import route as route_cohorts
from route_cohorts_id import route as route_cohorts_id
from route_cohorts_id_individuals import route as route_cohorts_id_individuals
from route_cohorts_id_filtering_terms import route as route_cohorts_id_filtering_terms

schemaRequestBody = json.load(open('./schemas/requestBody.json'))


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
            error_message = f'{error.message}'
            for part in list(error.path):
                error_message += f'/{part}'
            errors.append(error_message)

        if errors:
            return bad_request(errorMessage=', '.join(errors))

    if event["resource"] == "/cohorts":
        return route_cohorts(event)

    elif event['resource'] == '/cohorts/{id}':
        return route_cohorts_id(event)

    elif event['resource'] == '/cohorts/{id}/individuals':
        return route_cohorts_id_individuals(event)

    elif event['resource'] == '/cohorts/{id}/filtering_terms':
        return route_cohorts_id_filtering_terms(event)


if __name__ == '__main__':
    pass
