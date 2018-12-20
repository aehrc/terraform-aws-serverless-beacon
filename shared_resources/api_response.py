import json

HEADERS = {"Access-Control-Allow-Origin": "*"}


def bad_request(data, extra_params=None):
    response = {
        'error': {
            'errorCode': 400,
            'errorMessage': data,
        },
    }
    if extra_params:
        response.update(extra_params)
    return bundle_response(400, response)


def bundle_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': HEADERS,
        'body': json.dumps(body),
    }


def missing_parameter(*parameters):
    if len(parameters) > 1:
        required = "one of {}".format(', '.join(parameters))
    else:
        required = parameters[0]
    return "{} must be specified".format(required)
