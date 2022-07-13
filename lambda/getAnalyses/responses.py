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
    "response": {
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
        "numTotalResults": 100
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
        "exists": True
    }
}

# returning variants
g_variants_response = {
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
    "response": {
        "resultSets": [
            {
                "exists": False,
                "id": "datasetB",
                "results": [
                    {
                        "variantInternalId": "GRCh37-1-55505652-G-A",
                        "variation": {
                            "alternateBases": "A",
                            "location": {
                                "interval": {
                                    "end": {
                                        "type": "Number",
                                        "value": 5505653
                                    },
                                    "start": {
                                        "type": "Number",
                                        "value": 5505652
                                    },
                                    "type": "SequenceInterval"
                                },
                                "sequence_id": "refseq:NC_000001.10",
                                "type": "SequenceLocation"
                            },
                            "variantType": "SNP"
                        }
                    }
                ],
                "resultsCount": 1,
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
