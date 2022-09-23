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
            "pagination": {
                "currentPage": "",
                "limit": "",
                "nextPage": "",
                "previousPage": "",
                "skip": ""
            },
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
            "requestedGranularity": "boolean"  # TODO
        }
    },
    "responseSummary": {
        "exists": True # OUTPUT TARGET
    }
}


# Helpers start


def get_pagination_object(skip, limit):
    return {
        "limit": limit,
        "skip": skip
    }


def get_cursor_object(currentPage, nextPage, previousPage):
    return {
        "currentPage": currentPage,
        "nextPage": nextPage,
        "previousPage": previousPage,
    }


def get_result_sets_response(*, 
        reqAPI=BEACON_API_VERSION, 
        reqPagination={}, 
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
            "returnedGranularity": 'record',
            "receivedRequestSummary": {
                "apiVersion": reqAPI,
                "requestedSchemas": [], # TODO define this
                "pagination": reqPagination,
                "requestedGranularity": 'record'
            }
        },
        "response": { # OUTPUT TARGET
            "resultSets": [
                {
                    "exists": len(results) > 0,
                    "id": "redacted",
                    "results": results,
                    "resultsCount": len(results),
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


def get_counts_response(*, 
        reqAPI=BEACON_API_VERSION, 
        reqGranularity='count',
        exists=False,
        count=0):
    return {
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
                "apiVersion": reqAPI,  # TODO
                "requestedSchemas": [],  # TODO
                "pagination":{},
                "requestedGranularity": reqGranularity
            }
        },
        "responseSummary": {
            "exists": exists,
            "numTotalResults": count
        }
    }


def get_boolean_response(*, 
        reqAPI=BEACON_API_VERSION, 
        reqGranularity='boolean',
        exists=False):
    return {
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
                "apiVersion": reqAPI,  # TODO
                "requestedSchemas": [],  # TODO
                "pagination": {},  # TODO
                "requestedGranularity": reqGranularity
            }
        },
        "responseSummary": {
            "exists": exists
        }
    }

# Helpers end
