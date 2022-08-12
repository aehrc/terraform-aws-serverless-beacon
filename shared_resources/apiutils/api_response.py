import json, os

HEADERS = {"Access-Control-Allow-Origin": "*"}
BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']


def bad_request(*, apiVersion=None, errorMessage=None, filters=[], pagination={}, requestParameters=None, requestedSchemas=None):
    response = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "error": {
            "errorCode": 400,
            "errorMessage": f"{errorMessage}"
        },
        "meta": {
            "apiVersion": BEACON_API_VERSION,
            "beaconId": BEACON_ID,
            "receivedRequestSummary": {
                "apiVersion": apiVersion,
                "filters": filters,
                "pagination": pagination,
                "requestParameters": requestParameters,
                "requestedSchemas": requestedSchemas 
            },
            "returnedSchemas": []
        }
    }

    return bundle_response(400, response)


def bundle_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': HEADERS,
        'body': json.dumps(body),
    }


# think of a better way to do the following with python schema validation
def missing_parameter(*parameters):
    if len(parameters) > 1:
        required = "one of {}".format(', '.join(parameters))
    else:
        required = parameters[0]
    return "{} must be specified".format(required)
