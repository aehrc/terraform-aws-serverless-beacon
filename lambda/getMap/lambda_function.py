import json
import os

from api_response import bundle_response


def get_config():
    response = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "info": {},
        "meta": {
            "apiVersion": "string",
            "beaconId": "string",
            "returnedSchemas": [
                {
                    "entityType": "info",
                    "schema": "beacon-map-v2.0.0"
                }
            ]
        },
        "response": {
            "$schema": "../../configuration/beaconMapSchema.json",
            "endpointSets": {
                "dataset": {
                    "endpoints": {
                        "exampleEntries": {
                            "returnedEntryType": "exampleEntry",
                            "url": "https://exampleBeacons.org/datasets/{id}/exampleEntries"
                        }
                    },
                    "entryType": "dataset",
                    "filteringTermsUrl": "https://exampleBeacons.org/datasets/{id}/filteringTerms",
                    "openAPIEndpointsDefinition": "./datasets/endpoints.json",
                    "rootUrl": "https://exampleBeacons.org/datasets",
                    "singleEntryUrl": "https://exampleBeacons.org/datasets/{id}"
                },
                "exampleEntry": {
                    "entryType": "exampleEntry",
                    "filteringTermsUrl": "https://exampleBeacons.org/exampleEntries/{id}/filteringTerms",
                    "openAPIEndpointsDefinition": "./exampleEntries/endpoints.json",
                    "rootUrl": "https://exampleBeacons.org/exampleEntries",
                    "singleEntryUrl": "https://exampleBeacons.org/exampleEntries/{id}"
                }
            }
        }
    }
        

    return bundle_response(200, response)


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    response = get_config()
    print('Returning Response: {}'.format(json.dumps(response)))
    return response
