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

