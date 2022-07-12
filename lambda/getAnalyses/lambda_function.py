import json
import os

from api_response import bundle_response

BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']

def get_analyses(event):
    print(event)
    response = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "info": {

        },
        "meta": {
            "beaconId": BEACON_ID,
            "apiVersion": BEACON_API_VERSION,
            "returnedSchemas": [
                {
                    "entityType": "info",
                    "schema": "beacon-map-v2.0.0"
                }
            ],
            "returnedGranularity": "record",
            "receivedRequestSummary": {
                "apiVersion": "get from request", # TODO
                "requestedSchemas": [], # TODO
                "pagination": {}, # TODO
                "requestedGranularity": "record" # TODO
            }
        },
        "response": {
            "id": "some id",
            "setType": "dataset",
            "exists": True,
            "resultsCount": 1,
            "resultSets": [
                {
                    "exists": False,
                    "id": "datasetB",
                    "results": [
                        {
                            "id": "BEex3",
                            "name": "Basic Element example three",
                            "analysisDate": "2021-10-17",
                            "pipelineName": "Pipeline-panel-0001-v1"
                        },
                        {
                            "id": "BEex4",
                            "name": "Basic Element example four",
                            "analysisDate": "2021-10-17",
                            "pipelineName": "Pipeline-panel-0001-v1"
                        }
                    ],
                    "resultsCount": 2,
                    "resultsHandovers": [
                        {
                            "handoverType": {
                                "id": "EFO:0004157",
                                "label": "BAM format"
                            },
                            "note": "This handover link provides access to a summarized VCF.",
                            "url": "https://api.mygenomeservice.org/Handover/9dcc48d7-fc88-11e8-9110-b0c592dbf8c0"
                        }
                    ],
                    "setType": "dataset"
                }
            ]
        },
        "responseSummary": {
            "exists": True,
            "numTotalResults": 100
        }
    }

    return bundle_response(200, response)


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    response = get_analyses(event)
    print('Returning Response: {}'.format(json.dumps(response)))
    return response
