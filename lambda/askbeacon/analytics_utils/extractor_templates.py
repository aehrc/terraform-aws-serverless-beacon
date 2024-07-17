entity_extraction_template = {
    "query": {
        "pagination": {"skip": 0, "limit": 10},
        "filters": [],
        "requestedGranularity": "record",
    },
    "meta": {"apiVersion": "v2.0"},
}

variants_extraction_template = {
    "meta": {"apiVersion": "v2.0"},
    "query": {
        "pagination": {},
        "includeResultsetResponses": "HIT",
        "requestedGranularity": "record",
        "filters": [],
        "requestParameters": {
            "assemblyId": "GRCH38",
            "referenceBases": "N",
            "start": [],
            "end": [],
            "referenceName": "1",
        },
    },
}
