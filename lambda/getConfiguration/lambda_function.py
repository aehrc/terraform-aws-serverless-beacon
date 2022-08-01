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
            "$schema": "https://raw.githubusercontent.com/ga4gh-beacon/beacon-v2/main/framework/json/configuration/beaconConfigurationSchema.json",
            "entryTypes": {
                "genomicVariant": {
                    "additionallySupportedSchemas": [],
                    "defaultSchema": {
                        "id": "ga4gh-beacon-variant-v2.0.0",
                        "name": "Default schema for a genomic variation",
                        "referenceToSchemaDefinition": "https://exampleBeacons.org/genomicVariations/defaultSchema.json",
                        "schemaVersion": "v2.0.0"
                    },
                    "description": "The location of a sequence.",
                    "id": "genomicVariant",
                    "name": "Genomic Variants",
                    "ontologyTermForThisType": {
                        "id": "ENSGLOSSARY:0000092",
                        "label": "Variant"
                    },
                    "partOfSpecification": "Beacon v2.0.0"
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
