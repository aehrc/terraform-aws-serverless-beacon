# Getting started with test data

Please ensure you first upload the `chr1.vcf.gz` and `chr1.vcf.gz.tbi` files to an S3 bucket that is accessible from the sBeacon deployment account. Obtain the S3 URI for the `chr1.vcf.gz` from the uploaded desitation. Note that, both `vcf.gz` and `vcf.gz.tbi` files must have the same prefix in S3 for this to work.

Now edit the `submission.json` file such that they match the S3 URI of the `vcf.gz` file.

```json
...
    "vcfLocations": [
        "s3://<bucket>/<prefix>/chr1.vcf.gz"
    ]
...
```

## Data submission

You can submit the data in two ways.

### Submission as request body

You can simply copy the edited JSON content in to the API gateway `/submit` POST endpoint. If you're using a REST client make sure you add authorization headers before you make the request. For example, Postman supports Authorization type AWS Signature and there you can enter AWS Keys.

### Submission as an S3 payload

Alternatively, you can upload edited `submission.json` file to an S3 location accessible from deployment. Then you can use the file's S3 URI as follows in the API Gateway or in your REST client.

```json
{
    "s3Payload": "s3://<bucket>/<prefix>/submission.json"
}
```

This approach is recommended for larger submissions with thousands of metadata entries.

## API testing

### POST requst to `/g_variants` with following payload

```json
{
    "meta": {
        "apiVersion": "v2.0"
    },
    "query": {
        "pagination": {},
        "includeResultsetResponses": "HIT",
        "requestedGranularity": "record",
        "filters": [
        ],
        "requestParameters": {
            "assemblyId": "GRCH38",
            "start": [
                546801
            ],
            "end": [
                546810
            ],
            "referenceName": "1"
        }
    }
}
```

Result

```json
{
    "meta": {
        "beaconId": "au.csiro-serverless.beacon",
        "apiVersion": "v2.0.0",
        "returnedGranularity": "record",
        "receivedRequestSummary": {
            "apiVersion": "v2.0",
            "requestedSchemas": [],
            "filters": [],
            "req_params": {
                "assemblyId": "GRCH38",
                "start": [
                    546801
                ],
                "end": [
                    546810
                ],
                "referenceName": "1"
            },
            "includeResultsetResponses": "HIT",
            "pagination": {
                "skip": 0,
                "limit": 10
            },
            "requestedGranularity": "record",
            "testMode": false
        },
        "returnedSchemas": [
            {
                "entityType": "genomicVariation",
                "schema": "beacon-g_variant-v2.0.0"
            }
        ]
    },
    "responseSummary": {
        "exists": true,
        "numTotalResults": 2
    },
    "response": {
        "resultSets": [
            {
                "id": "",
                "setType": "",
                "exists": true,
                "resultsCount": 2,
                "results": [
                    {
                        "variantInternalId": "R1JDSDM4CTEJNTQ2ODAyCUcJQw==",
                        "variation": {
                            "referenceBases": "G",
                            "alternateBases": "C",
                            "location": {
                                "interval": {
                                    "start": {
                                        "type": "Number",
                                        "value": 546802
                                    },
                                    "end": {
                                        "type": "Number",
                                        "value": 546803
                                    },
                                    "type": "SequenceInterval"
                                },
                                "sequence_id": "GRCH38",
                                "type": "SequenceLocation"
                            },
                            "variantType": "SNP"
                        }
                    },
                    {
                        "variantInternalId": "R1JDSDM4CTEJNTQ2ODA1CVQJQw==",
                        "variation": {
                            "referenceBases": "T",
                            "alternateBases": "C",
                            "location": {
                                "interval": {
                                    "start": {
                                        "type": "Number",
                                        "value": 546805
                                    },
                                    "end": {
                                        "type": "Number",
                                        "value": 546806
                                    },
                                    "type": "SequenceInterval"
                                },
                                "sequence_id": "GRCH38",
                                "type": "SequenceLocation"
                            },
                            "variantType": "SNP"
                        }
                    }
                ],
                "resultsHandover": null
            }
        ]
    },
    "beaconHandovers": []
}
```

### POST request to `/g_variants/R1JDSDM4CTEJNTQ2ODAyCUcJQw==/individuals` with following payload

```json
{
    "meta": {
        "apiVersion": "v2.0"
    },
    "query": {
        "requestedGranularity": "record",
        "pagination": {
            "limit": 1
        },
        "filters": []
    }
}
```

Result

```json
{
    "meta": {
        "beaconId": "au.csiro-serverless.beacon",
        "apiVersion": "v2.0.0",
        "returnedGranularity": "record",
        "receivedRequestSummary": {
            "apiVersion": "v2.0",
            "requestedSchemas": [],
            "filters": [],
            "req_params": {},
            "includeResultsetResponses": "HIT",
            "pagination": {
                "skip": 0,
                "limit": 1
            },
            "requestedGranularity": "record",
            "testMode": false
        },
        "returnedSchemas": [
            {
                "entityType": "individual",
                "schema": "beacon-individual-v2.0.0"
            }
        ]
    },
    "responseSummary": {
        "exists": true,
        "numTotalResults": 9
    },
    "response": {
        "resultSets": [
            {
                "id": "",
                "setType": "",
                "exists": true,
                "resultsCount": 9,
                "results": [
                    {
                        "diseases": [
                            {
                                "diseaseCode": {
                                    "id": "SNOMED:56265001",
                                    "label": "Heart disease (disorder)"
                                }
                            }
                        ],
                        "ethnicity": {
                            "id": "SNOMED:17789004",
                            "label": "Papuans"
                        },
                        "exposures": "",
                        "geographicOrigin": {
                            "id": "SNOMED:223713009",
                            "label": "Argentina"
                        },
                        "id": "UNQ_1-6",
                        "info": "",
                        "interventionsOrProcedures": [
                            {
                                "procedureCode": {
                                    "id": "NCIT:C93025"
                                }
                            }
                        ],
                        "karyotypicSex": "XX",
                        "measures": "",
                        "pedigrees": "",
                        "phenotypicFeatures": "",
                        "sex": {
                            "id": "SNOMED:248152002",
                            "label": "Female"
                        },
                        "treatments": ""
                    }
                ],
                "resultsHandover": null
            }
        ]
    },
    "beaconHandovers": []
}
```

### POST request to `/individuals` with following payload

```json
{
    "query": {
        "filters": [
            {
                "id": "SNOMED:223688001"
            }
        ],
        "requestedGranularity": "count"
    },
    "meta": {
        "apiVersion": "v2.0"
    }
}
```

Result

```json
{
    "meta": {
        "beaconId": "au.csiro-serverless.beacon",
        "apiVersion": "v2.0.0",
        "returnedGranularity": "count",
        "receivedRequestSummary": {
            "apiVersion": "v2.0",
            "requestedSchemas": [],
            "filters": [
                {
                    "id": "SNOMED:223688001"
                }
            ],
            "req_params": {},
            "includeResultsetResponses": "HIT",
            "pagination": {
                "skip": 0,
                "limit": 10
            },
            "requestedGranularity": "count",
            "testMode": false
        },
        "returnedSchemas": [
            {
                "entityType": "individual",
                "schema": "beacon-individual-v2.0.0"
            }
        ]
    },
    "responseSummary": {
        "exists": true,
        "numTotalResults": 4
    },
    "beaconHandovers": []
}
```