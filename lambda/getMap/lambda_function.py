import json
import os

from apiutils.api_response import bundle_response


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
                "analysis": {
                    "endpoints": {
                        "genomicVariant": {
                            "returnedEntryType": "genomicVariant",
                            "url": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/analyses/{id}/g_variants"
                        }
                    },
                    "entryType": "analysis",
                    "openAPIEndpointsDefinition": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/analyses/endpoints.json",
                    "rootUrl": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/analyses",
                    "singleEntryUrl": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/analyses/{id}"
                },
                "biosample": {
                    "endpoints": {
                        "analysis": {
                            "returnedEntryType": "analysis",
                            "url": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/biosamples/{id}/analyses"
                        },
                        "genomicVariant": {
                            "returnedEntryType": "genomicVariant",
                            "url": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/biosamples/{id}/g_variants"
                        },
                        "run": {
                            "returnedEntryType": "run",
                            "url": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/biosamples/{id}/runs"
                        }
                    },
                    "entryType": "biosample",
                    "openAPIEndpointsDefinition": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/biosamples/endpoints.json",
                    "rootUrl": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/biosamples",
                    "singleEntryUrl": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/biosamples/{id}"
                },
                "cohort": {
                    "endpoints": {
                        "analyses": {
                            "returnedEntryType": "analysis",
                            "url": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/cohorts/{id}/analyses"
                        },
                        "biosample": {
                            "returnedEntryType": "biosample",
                            "url": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/cohorts/{id}/biosamples"
                        },
                        "genomicVariant": {
                            "returnedEntryType": "genomicVariant",
                            "url": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/cohorts/{id}/g_variants"
                        },
                        "individual": {
                            "returnedEntryType": "individual",
                            "url": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/cohorts/{id}/individuals"
                        },
                        "runs": {
                            "returnedEntryType": "run",
                            "url": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/cohorts/{id}/runs"
                        }
                    },
                    "entryType": "cohort",
                    "filteringTermsUrl": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/cohorts/{id}/filtering_terms",
                    "openAPIEndpointsDefinition": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/cohorts/endpoints.json",
                    "rootUrl": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/cohorts",
                    "singleEntryUrl": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/cohorts/{id}"
                },
                "dataset": {
                    "endpoints": {
                        "analyses": {
                            "returnedEntryType": "analysis",
                            "url": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/datasets/{id}/analyses"
                        },
                        "biosample": {
                            "returnedEntryType": "biosample",
                            "url": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/datasets/{id}/biosamples"
                        },
                        "genomicVariant": {
                            "returnedEntryType": "genomicVariant",
                            "url": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/datasets/{id}/g_variants"
                        },
                        "individual": {
                            "returnedEntryType": "individual",
                            "url": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/datasets/{id}/individuals"
                        },
                        "runs": {
                            "returnedEntryType": "run",
                            "url": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/datasets/{id}/runs"
                        }
                    },
                    "entryType": "dataset",
                    "filteringTermsUrl": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/datasets/{id}/filtering_terms",
                    "openAPIEndpointsDefinition": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/datasets/endpoints.json",
                    "rootUrl": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/datasets",
                    "singleEntryUrl": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/datasets/{id}"
                },
                "genomicVariant": {
                    "endpoints": {
                        "analyses": {
                            "returnedEntryType": "analysis",
                            "url": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/g_variants/{id}/analyses"
                        },
                        "biosample": {
                            "returnedEntryType": "biosample",
                            "url": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/g_variants/{id}/biosamples"
                        },
                        "individual": {
                            "returnedEntryType": "individual",
                            "url": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/g_variants/{id}/individuals"
                        },
                        "runs": {
                            "returnedEntryType": "run",
                            "url": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/g_variants/{id}/runs"
                        }
                    },
                    "entryType": "genomicVariant",
                    "openAPIEndpointsDefinition": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/genomicVariations/endpoints.json",
                    "rootUrl": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/g_variants",
                    "singleEntryUrl": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/g_variants/{id}"
                },
                "individual": {
                    "endpoints": {
                        "analyses": {
                            "returnedEntryType": "analysis",
                            "url": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/individuals/{id}/analyses"
                        },
                        "biosample": {
                            "returnedEntryType": "biosample",
                            "url": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/individuals/{id}/biosamples"
                        },
                        "genomicVariant": {
                            "returnedEntryType": "genomicVariant",
                            "url": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/individuals/{id}/g_variants"
                        },
                        "runs": {
                            "returnedEntryType": "run",
                            "url": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/individuals/{id}/runs"
                        }
                    },
                    "entryType": "individual",
                    "filteringTermsUrl": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/individuals/{id}/filtering_terms",
                    "openAPIEndpointsDefinition": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/individuals/endpoints.json",
                    "rootUrl": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/individuals",
                    "singleEntryUrl": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/individuals/{id}"
                },
                "run": {
                    "endpoints": {
                        "analysis": {
                            "returnedEntryType": "analysis",
                            "url": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/runs/{id}/analyses"
                        },
                        "genomicVariant": {
                            "returnedEntryType": "genomicVariant",
                            "url": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/runs/{id}/g_variants"
                        }
                    },
                    "entryType": "run",
                    "openAPIEndpointsDefinition": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/runs/endpoints.json",
                    "rootUrl": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/runs",
                    "singleEntryUrl": "https://ip35zfam3d.execute-api.us-east-1.amazonaws.com/prod/runs/{id}"
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
