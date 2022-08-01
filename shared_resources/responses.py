import os

BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']

'''
This document contains sample responses needed by this API endpoint
'''

# returning multiple analyses
result_sets_response = {
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
            "apiVersion": "get from request",  # TODO
            "requestedSchemas": [],  # TODO
            "pagination": {},  # TODO
            "requestedGranularity": "record"  # TODO
        }
    },
    "response": { # OUTPUT TARGET
        "resultSets": [
            {
                "exists": False,
                "id": "datasetB",
                "results": [

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


# helper function
def get_result_sets_response(*, 
        reqAPI=BEACON_API_VERSION, 
        reqGranularity='boolean', 
        reqPagination={}, 
        resGranularity='boolean', 
        results=[], 
        setType=None, 
        info={},
        exists=False,
        total=0):

    return { 
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "info": info,
        "meta": {
            "beaconId": BEACON_ID,
            "apiVersion": BEACON_API_VERSION,
            "returnedSchemas": [
                {
                    "entityType": "info",
                    "schema": "beacon-map-v2.0.0"
                }
            ],
            "returnedGranularity": resGranularity,
            "receivedRequestSummary": {
                "apiVersion": reqAPI,
                "requestedSchemas": [], # TODO define this
                "pagination": reqPagination,
                "requestedGranularity": reqGranularity
            }
        },
        "response": { # OUTPUT TARGET
            "resultSets": [
                {
                    "exists": False,
                    "id": "datasetB",
                    "results": results,
                    "resultsCount": 2,
                    "resultsHandovers": [], # TODO update when available
                    "setType": setType
                }
            ]
        },
        "responseSummary": {
            "exists": exists,
            "numTotalResults": total
        }
    }

# returning counts
counts_response = {
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
        "returnedGranularity": "count",
        "receivedRequestSummary": {
            "apiVersion": "get from request",  # TODO
            "requestedSchemas": [],  # TODO
            "pagination": {},  # TODO
            "requestedGranularity": "record"  # TODO
        }
    },
    "responseSummary": {
        "exists": True,
        "numTotalResults": 100 # OUTPUT TARGET
    }
}

# returning boolean
boolean_response = {
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
        "returnedGranularity": "boolean",
        "receivedRequestSummary": {
            "apiVersion": "get from request",  # TODO
            "requestedSchemas": [],  # TODO
            "pagination": {},  # TODO
            "requestedGranularity": "record"  # TODO
        }
    },
    "responseSummary": {
        "exists": True # OUTPUT TARGET
    }
}
