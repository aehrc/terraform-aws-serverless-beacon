import json

from apiutils.api_response import bundle_response


BEACON_URL = 'https://api.beacon.csiro.au'
MODEL_URL = 'https://github.com/ga4gh-beacon/beacon-v2/tree/main/models/json/beacon-v2-default-model'


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
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "endpointSets": {
                "analysis": {
                    "endpoints": {
                        "genomicVariant": {
                            "returnedEntryType": "genomicVariant",
                            "url": f"{BEACON_URL}/analyses/{{id}}/g_variants"
                        }
                    },
                    "entryType": "analysis",
                    "filteringTermsUrl": f"{BEACON_URL}/analyses/filtering_terms",
                    "openAPIEndpointsDefinition": f"{MODEL_URL}/analyses/endpoints.json",
                    "rootUrl": f"{BEACON_URL}/analyses",
                    "singleEntryUrl": f"{BEACON_URL}/analyses/{{id}}"
                },
                "biosample": {
                    "endpoints": {
                        "analysis": {
                            "returnedEntryType": "analysis",
                            "url": f"{BEACON_URL}/biosamples/{{id}}/analyses"
                        },
                        "genomicVariant": {
                            "returnedEntryType": "genomicVariant",
                            "url": f"{BEACON_URL}/biosamples/{{id}}/g_variants"
                        },
                        "run": {
                            "returnedEntryType": "run",
                            "url": f"{BEACON_URL}/biosamples/{{id}}/runs"
                        }
                    },
                    "entryType": "biosample",
                    "filteringTermsUrl": f"{BEACON_URL}/biosamples/filtering_terms",
                    "openAPIEndpointsDefinition": f"{MODEL_URL}/biosamples/endpoints.json",
                    "rootUrl": f"{BEACON_URL}/biosamples",
                    "singleEntryUrl": f"{BEACON_URL}/biosamples/{{id}}"
                },
                "cohort": {
                    "endpoints": {
                        "analyses": {
                            "returnedEntryType": "analysis",
                            "url": f"{BEACON_URL}/cohorts/{{id}}/analyses"
                        },
                        "biosample": {
                            "returnedEntryType": "biosample",
                            "url": f"{BEACON_URL}/cohorts/{{id}}/biosamples"
                        },
                        "genomicVariant": {
                            "returnedEntryType": "genomicVariant",
                            "url": f"{BEACON_URL}/cohorts/{{id}}/g_variants"
                        },
                        "individual": {
                            "returnedEntryType": "individual",
                            "url": f"{BEACON_URL}/cohorts/{{id}}/individuals"
                        },
                        "runs": {
                            "returnedEntryType": "run",
                            "url": f"{BEACON_URL}/cohorts/{{id}}/runs"
                        }
                    },
                    "entryType": "cohort",
                    "filteringTermsUrl": f"{BEACON_URL}/cohorts/{{id}}/filtering_terms",
                    "openAPIEndpointsDefinition": f"{MODEL_URL}/cohorts/endpoints.json",
                    "rootUrl": f"{BEACON_URL}/cohorts",
                    "singleEntryUrl": f"{BEACON_URL}/cohorts/{{id}}"
                },
                "dataset": {
                    "endpoints": {
                        "analyses": {
                            "returnedEntryType": "analysis",
                            "url": f"{BEACON_URL}/datasets/{{id}}/analyses"
                        },
                        "biosample": {
                            "returnedEntryType": "biosample",
                            "url": f"{BEACON_URL}/datasets/{{id}}/biosamples"
                        },
                        "genomicVariant": {
                            "returnedEntryType": "genomicVariant",
                            "url": f"{BEACON_URL}/datasets/{{id}}/g_variants"
                        },
                        "individual": {
                            "returnedEntryType": "individual",
                            "url": f"{BEACON_URL}/datasets/{{id}}/individuals"
                        },
                        "runs": {
                            "returnedEntryType": "run",
                            "url": f"{BEACON_URL}/datasets/{{id}}/runs"
                        }
                    },
                    "entryType": "dataset",
                    "filteringTermsUrl": f"{BEACON_URL}/datasets/{{id}}/filtering_terms",
                    "openAPIEndpointsDefinition": f"{MODEL_URL}/datasets/endpoints.json",
                    "rootUrl": f"{BEACON_URL}/datasets",
                    "singleEntryUrl": f"{BEACON_URL}/datasets/{{id}}"
                },
                "genomicVariant": {
                    "endpoints": {
                        "analyses": {
                            "returnedEntryType": "analysis",
                            "url": f"{BEACON_URL}/g_variants/{{id}}/analyses"
                        },
                        "biosample": {
                            "returnedEntryType": "biosample",
                            "url": f"{BEACON_URL}/g_variants/{{id}}/biosamples"
                        },
                        "individual": {
                            "returnedEntryType": "individual",
                            "url": f"{BEACON_URL}/g_variants/{{id}}/individuals"
                        },
                        "runs": {
                            "returnedEntryType": "run",
                            "url": f"{BEACON_URL}/g_variants/{{id}}/runs"
                        }
                    },
                    "entryType": "genomicVariant",
                    "openAPIEndpointsDefinition": f"{MODEL_URL}/genomicVariations/endpoints.json",
                    "rootUrl": f"{BEACON_URL}/g_variants",
                    "singleEntryUrl": f"{BEACON_URL}/g_variants/{{id}}"
                },
                "individual": {
                    "endpoints": {
                        "analyses": {
                            "returnedEntryType": "analysis",
                            "url": f"{BEACON_URL}/individuals/{{id}}/analyses"
                        },
                        "biosample": {
                            "returnedEntryType": "biosample",
                            "url": f"{BEACON_URL}/individuals/{{id}}/biosamples"
                        },
                        "genomicVariant": {
                            "returnedEntryType": "genomicVariant",
                            "url": f"{BEACON_URL}/individuals/{{id}}/g_variants"
                        },
                        "runs": {
                            "returnedEntryType": "run",
                            "url": f"{BEACON_URL}/individuals/{{id}}/runs"
                        }
                    },
                    "entryType": "individual",
                    "filteringTermsUrl": f"{BEACON_URL}/individuals/filtering_terms",
                    # "filteringTermsUrl": f"{BEACON_URL}/individuals/{{id}}/filtering_terms",
                    "openAPIEndpointsDefinition": f"{MODEL_URL}/individuals/endpoints.json",
                    "rootUrl": f"{BEACON_URL}/individuals",
                    "singleEntryUrl": f"{BEACON_URL}/individuals/{{id}}"
                },
                "run": {
                    "endpoints": {
                        "analysis": {
                            "returnedEntryType": "analysis",
                            "url": f"{BEACON_URL}/runs/{{id}}/analyses"
                        },
                        "genomicVariant": {
                            "returnedEntryType": "genomicVariant",
                            "url": f"{BEACON_URL}/runs/{{id}}/g_variants"
                        }
                    },
                    "entryType": "run",
                    "filteringTermsUrl": f"{BEACON_URL}/runs/filtering_terms",
                    "openAPIEndpointsDefinition": f"{MODEL_URL}/runs/endpoints.json",
                    "rootUrl": f"{BEACON_URL}/runs",
                    "singleEntryUrl": f"{BEACON_URL}/runs/{{id}}"
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
