import json
import os

from apiutils.api_response import bundle_response


def get_entry_types():
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
            "$schema": "../../configuration/entryTypesSchema.json",
            "entryTypes": {
                "dataset": {
                    "aCollectionOf": [
                        {
                            "id": "exampleEntry",
                            "name": "Example entries"
                        }
                    ],
                    "additionallySupportedSchemas": [],
                    "defaultSchema": {
                        "id": "datasetDefaultSchema",
                        "name": "Default schema for datasets",
                        "referenceToSchemaDefinition": "./datasets/defaultSchema.json",
                        "schemaVersion": "v.2"
                    },
                    "description": "A Dataset is a collection of records, like rows in a database or cards in a cardholder.",
                    "endpoint": "/datasets",
                    "filteringTermsReference": "./datasets/filteringTerms.json",
                    "id": "dataset",
                    "name": "Dataset",
                    "ontologyTermForThisType": {
                        "id": "NCIT:C47824",
                        "label": "Data set"
                    },
                    "partOfSpecification": "Beacon v2.0"
                },
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
                },
                "individual": {
                    
                },
                "biosample": {
                    
                }
            }
        }
    }

    return bundle_response(200, response)


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    response = get_entry_types()
    print('Returning Response: {}'.format(json.dumps(response)))
    return response
