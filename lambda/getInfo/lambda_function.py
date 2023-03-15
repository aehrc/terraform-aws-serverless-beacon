import json
import os
from time import time
from datetime import datetime

from apiutils.api_response import bundle_response


BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
VERSION = os.environ['VERSION']
BEACON_ID = os.environ['BEACON_ID']
BEACON_NAME = os.environ['BEACON_NAME']
ORGANISATION_ID = os.environ['ORGANISATION_ID']
ORGANISATION_NAME = os.environ['ORGANISATION_NAME']


def get_info():
    response = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "info": {},
        "meta": {
            "apiVersion": BEACON_API_VERSION,
            "beaconId": BEACON_ID,
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


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    response = get_info()
    print('Returning Response: {}'.format(json.dumps(response)))
    return response
