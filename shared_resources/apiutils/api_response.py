import json
import os

from smart_open import open as sopen


HEADERS = {"Access-Control-Allow-Origin": "*"}
BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']
METADATA_BUCKET = os.environ['METADATA_BUCKET']


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


def bundle_response(status_code, body, query_id=None):
    if query_id:
        with sopen(f's3://{METADATA_BUCKET}/query-responses/{query_id}.json', 'w') as s3f:
            json.dump(body, s3f)
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


def fetch_from_cache(query_id):
    with sopen(f's3://{METADATA_BUCKET}/query-responses/{query_id}.json') as s3f:
        return json.load(s3f)
