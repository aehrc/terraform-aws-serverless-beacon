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
            "$schema": "https://github.com/ga4gh-beacon/beacon-v2/blob/main/framework/json/configuration/entryTypesSchema.json",
            "entryTypes": {
                "analysis": {
                    "additionallySupportedSchemas": [],
                    "defaultSchema": {
                        "id": "ga4gh-beacon-analysis-v2.0.0",
                        "name": "Default schema for a bioinformatics analysis",
                        "referenceToSchemaDefinition": "https://github.com/ga4gh-beacon/beacon-v2/blob/main/models/json/beacon-v2-default-model/analyses/defaultSchema.json",
                        "schemaVersion": "v2.0.0"
                    },
                    "description": "Apply analytical methods to existing data of a specific type.",
                    "id": "analysis",
                    "name": "Bioinformatics analysis",
                    "ontologyTermForThisType": {
                        "id": "edam:operation_2945",
                        "label": "Analysis"
                    },
                    "partOfSpecification": "Beacon v2.0.0"
                },
                "biosample": {
                    "additionallySupportedSchemas": [],
                    "defaultSchema": {
                        "id": "ga4gh-beacon-biosample-v2.0.0",
                        "name": "Default schema for a biological sample",
                        "referenceToSchemaDefinition": "https://github.com/ga4gh-beacon/beacon-v2/blob/main/models/json/beacon-v2-default-model/biosamples/defaultSchema.json",
                        "schemaVersion": "v2.0.0"
                    },
                    "description": "Any material sample taken from a biological entity for testing, diagnostic, propagation, treatment or research purposes, including a sample obtained from a living organism or taken from the biological object after halting of all its life functions. Biospecimen can contain one or more components including but not limited to cellular molecules, cells, tissues, organs, body fluids, embryos, and body excretory products. [ NCI ]",
                    "id": "biosample",
                    "name": "Biological Sample",
                    "ontologyTermForThisType": {
                        "id": "NCIT:C70699",
                        "label": "Biospecimen"
                    },
                    "partOfSpecification": "Beacon v2.0.0"
                },
                "cohort": {
                    "aCollectionOf": [
                        {
                            "id": "individual",
                            "name": "Individuals"
                        }
                    ],
                    "additionalSupportedSchemas": [],
                    "defaultSchema": {
                        "id": "ga4gh-beacon-cohort-v2.0.0",
                        "name": "Default schema for cohorts",
                        "referenceToSchemaDefinition": "https://github.com/ga4gh-beacon/beacon-v2/blob/main/models/json/beacon-v2-default-model/cohorts/defaultSchema.json",
                        "schemaVersion": "v2.0.0"
                    },
                    "description": "A group of individuals, identified by a common characteristic. [ NCI ]",
                    "id": "cohort",
                    "name": "Cohort",
                    "ontologyTermForThisType": {
                        "id": "NCIT:C61512",
                        "label": "Cohort"
                    },
                    "partOfSpecification": "Beacon v2.0.0"
                },
                "dataset": {
                    "aCollectionOf": [
                        {
                            "id": "genomicVariant",
                            "name": "Genomic Variants"
                        }
                    ],
                    "additionalSupportedSchemas": [],
                    "defaultSchema": {
                        "id": "ga4gh-beacon-dataset-v2.0.0",
                        "name": "Default schema for datasets",
                        "referenceToSchemaDefinition": "https://github.com/ga4gh-beacon/beacon-v2/blob/main/models/json/beacon-v2-default-model/datasets/defaultSchema.json",
                        "schemaVersion": "v2.0.0"
                    },
                    "description": "A Dataset is a collection of related sets of information, e.g. genomic variations together with associated procedural and biological metadata. In a Beacon context, a datasets may consist of information generated in a specific study or project, or represent the main content of the Beacon resource.",
                    "id": "dataset",
                    "name": "Dataset",
                    "ontologyTermForThisType": {
                        "id": "NCIT:C47824",
                        "label": "Data set"
                    },
                    "partOfSpecification": "Beacon v2.0.0"
                },
                "genomicVariant": {
                    "additionallySupportedSchemas": [],
                    "defaultSchema": {
                        "id": "ga4gh-beacon-variant-v2.0.0",
                        "name": "Default schema for a genomic variation",
                        "referenceToSchemaDefinition": "https://github.com/ga4gh-beacon/beacon-v2/blob/main/models/json/beacon-v2-default-model/genomicVariations/defaultSchema.json",
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
                    "additionallySupportedSchemas": [],
                    "defaultSchema": {
                        "id": "ga4gh-beacon-individual-v2.0.0",
                        "name": "Default schema for an individual",
                        "referenceToSchemaDefinition": "https://github.com/ga4gh-beacon/beacon-v2/blob/main/models/json/beacon-v2-default-model/individuals/defaultSchema.json",
                        "schemaVersion": "v2.0.0"
                    },
                    "description": "A human being. It could be a Patient, a Tissue Donor, a Participant, a Human Study Subject, etc.",
                    "id": "individual",
                    "name": "Individual",
                    "ontologyTermForThisType": {
                        "id": "NCIT:C25190",
                        "label": "Person"
                    },
                    "partOfSpecification": "Beacon v2.0.0"
                },
                "run": {
                    "additionallySupportedSchemas": [],
                    "defaultSchema": {
                        "id": "ga4gh-beacon-run-v2.0.0",
                        "name": "Default schema for a sequencing run",
                        "referenceToSchemaDefinition": "https://github.com/ga4gh-beacon/beacon-v2/blob/main/models/json/beacon-v2-default-model/runs/defaultSchema.json",
                        "schemaVersion": "v2.0.0"
                    },
                    "description": "The valid and completed operation of a high-throughput sequencing instrument for a single sequencing process. [ NCI ]",
                    "id": "run",
                    "name": "Sequencing run",
                    "ontologyTermForThisType": {
                        "id": "NCIT:C148088",
                        "label": "Sequencing run"
                    },
                    "partOfSpecification": "Beacon v2.0.0"
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
