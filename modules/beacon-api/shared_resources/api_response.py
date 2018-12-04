import json

HEADERS = {"Access-Control-Allow-Origin": "*"}


def bad_request(data):
    return bundle_response(400, {'data': data})


def bundle_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': HEADERS,
        'body': json.dumps(body),
    }

