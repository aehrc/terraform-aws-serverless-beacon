import json
import os
from time import time
from datetime import datetime

from api_response import bundle_response

BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
VERSION = os.environ['VERSION']
BEACON_ID = os.environ['BEACON_ID']
BEACON_NAME = os.environ['BEACON_NAME']
DATASETS_TABLE = os.environ['DATASETS_TABLE']
ORGANISATION_ID = os.environ['ORGANISATION_ID']
ORGANISATION_NAME = os.environ['ORGANISATION_NAME']


def get_info():
    response = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "info": {},
        "meta": {
            "apiVersion": "string",
            "beaconId": "string",
            "returnedSchemas": [
                {
                    "entityType": "info",
                    "schema": "beacon-info-v2.0.0"
                }
            ]
        },
        "response": {
            "alternativeUrl": "https://bioinformatics.csiro.au/",
            "apiVersion": BEACON_API_VERSION,
            "createDateTime": datetime.fromtimestamp(time()).isoformat(),
            "description": "This is the Serverless Beacon from CSIRO",
            "environment": "dev",
            "id": BEACON_ID,
            "info": {
                "additionalInfoKey1": "additionalInfoValue1",
                "additionalInfoKey2": [
                    "additionalInfoValue2",
                    "additionalInfoValue3"
                ]
            },
            "name":BEACON_NAME,
            "organization": {
                "address": "string",
                "contactUrl": "string",
                "description": "string",
                "id": ORGANISATION_ID,
                "info": {},
                "logoUrl": "string",
                "name": ORGANISATION_NAME,
                "welcomeUrl": "string"
            },
            "updateDateTime": datetime.fromtimestamp(time()).isoformat(),
            "version": VERSION,
            "welcomeUrl": "https://bioinformatics.csiro.au/"
        }
    }

    return bundle_response(200, response)

# keeping for other API updates
# return {
#     "id": BEACON_ID,
#     "name": BEACON_NAME,
#     "apiVersion": BEACON_API_VERSION,
#     "organization": {
#         "id": ORGANISATION_ID,
#         "name": ORGANISATION_NAME
#     },
#     "datasets": [
#         {
#             "id": item['id']['S'],
#             "name": item['name']['S'],
#             "assemblyId": item['assemblyId']['S'],
#             "createDateTime": item['createDateTime']['S'],
#             "updateDateTime": item['updateDateTime']['S'],
#             "description": item.get('description', {}).get('S') or None,
#             "version": item.get('version', {}).get('S') or None,
#             "variantCount": item.get('variantCount', {}).get('N') or None,
#             "callCount": item.get('callCount', {}).get('N') or None,
#             "sampleCount": item.get('sampleCount', {}).get('N') or None,
#             "info": item.get('info', {}).get('L') or None,
#             "dataUseConditions": item.get('dataUseConditions', {}
#                                           ).get('M') or None,
#             "externalUrl": item.get('externalUrl', {}).get('S') or None,
#         } for item in items
#     ]
# }


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    response = get_info()
    print('Returning Response: {}'.format(json.dumps(response)))
    return response
