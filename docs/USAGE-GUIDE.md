## Contents
<!-- TOC start (generated with https://github.com/derlin/bitdowntoc) -->

- [Getting started with test data](#getting-started-with-test-data)
- [Data submission](#data-submission)
  * [Option 1: Submission as request body](#option-1-submission-as-request-body)
  * [Option 2: Submission as an S3 payload](#option-2-submission-as-an-s3-payload)
- [API usage](#api-usage)
  * [POST requst to `/g_variants` with following payload](#post-requst-to-g_variants-with-following-payload)
  * [POST request to `/g_variants/R1JDSDM4CTEJNTQ2ODAyCUcJQw==/individuals` with following payload](#post-request-to-g_variantsr1jdsdm4ctejntq2odaycucjqwindividuals-with-following-payload)
  * [POST request to `/individuals` with following payload](#post-request-to-individuals-with-following-payload)

<!-- TOC end -->

## Getting started with test data

Please ensure you first upload the `chr1.vcf.gz` and `chr1.vcf.gz.tbi` files to an S3 bucket that is accessible from the sBeacon deployment account. Obtain the S3 URI for the `chr1.vcf.gz` from the uploaded desitation. Note that, both `vcf.gz` and `vcf.gz.tbi` files must have the same prefix in S3 for this to work. Please note that, all the buckets you create in AWS are in the same region as the deployment.

Now edit the [`submission.json`](../examples/test-data/submission.json) using the S3 URI of the `vcf.gz` file.

```json
{
    // other fields
    "vcfLocations": [
        "s3://<bucket>/<prefix>/chr1.vcf.gz"
    ],
    // other fields
}
```

## Data submission

You can submit this data in two ways.

### Option 1: Submission as request body

You can simply copy the edited JSON content in to the API gateway `/submit_dataset` POST endpoint. If you're using a REST client make sure you add authorization headers before you make the request. For example, Postman supports Authorization type AWS Signature and there you can enter AWS Keys.

### Option 2: Submission as an S3 payload

Alternatively, you can upload edited [`submission.json`](../examples/test-data/submission.json) file to an S3 location accessible from deployment. Then you can use the file's S3 URI as follows in the API Gateway or in your REST client.

```json
{
    "s3Payload": "s3://<bucket>/<prefix>/submission.json"
}
```

Option 2 is recommended for larger submissions with thousands of metadata entries.

## API usage

### POST requst to `/g_variants` with following payload

**Query**

Schema for the `query.requestParameters` attribute is available at [../shared_resources/schemas/g-variants-request-parameters.json](../shared_resources/schemas/g-variants-request-parameters.json).

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

**Result**

Result follows the `genomic variations` models which has the schema presented at [../shared_resources/schemas/genomic-variation-schema.json](../shared_resources/schemas/genomic-variation-schema.json).

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

**Query**
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

**Result**

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

**Query**
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

**Result**

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
