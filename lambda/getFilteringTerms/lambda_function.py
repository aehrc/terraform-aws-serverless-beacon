import json
import os
import base64

from dynamodb.onto_index import OntoData

from apiutils.api_response import bundle_response


BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']
METADATA_BUCKET = os.environ['METADATA_BUCKET']


def get_entry_types(terms, limit=500, nextPage=None, previousPage=None):
    response =     {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "info": {},
        "meta": {
            "apiVersion": BEACON_API_VERSION,
            "beaconId": BEACON_ID,
            "returnedSchemas": [],
            "receivedRequestSummary": {
                "apiVersion": "get from request",  # TODO
                "requestedSchemas": [],  # TODO
                "pagination": {
                    "limit": limit,
                    "nextPage": nextPage,
                    "previousPage": previousPage,
                },
                "requestedGranularity": "record"  # TODO
            }
        },
        "response": {
            "filteringTerms": terms,
            "resources": [
                {
                    "id": "NA",
                    "iriPrefix": "NA",
                    "name": "NA",
                    "namespacePrefix": "NA",
                    "url": "NA",
                    "version": "TBD"
                }
            ]
        }
    }

    return bundle_response(200, response)


def lambda_handler(event, context):
    if (event['httpMethod'] == 'GET'):
        params = event['queryStringParameters'] or dict()
        skip = params.get("skip", None)
        limit = params.get("limit", None)
        
    results = OntoData.scan(limit=limit)
    response = get_entry_types(
        sorted(
            [
                {
                'id': result.term,
                'label': result.label,
                'type': result.type,
                } 
                for result in results
            ],
            key=lambda x: x['id']
        )
    )
    print('Returning Response: {}'.format(json.dumps(response)))
    return response


if __name__ == '__main__':
    pass
