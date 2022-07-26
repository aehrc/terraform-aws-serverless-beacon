analysis_entry  = {
    "id": "BEex3",
    "name": "Basic Element example three",
    "analysisDate": "2021-10-17",
    "pipelineName": "Pipeline-panel-0001-v1"
}

biosample_entry = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "biosampleStatus": {
        "id": "EFO:0009655",
        "label": "abnormal sample"
    },
    "collectionDate": "2020-09-11",
    "collectionMoment": "P32Y6M1D",
    "id": "sample-example-0001",
    "obtentionProcedure": {
        "procedureCode": {
            "id": "OBI:0002654",
            "label": "needle biopsy"
        }
    },
    "sampleOriginType": {
        "id": "UBERON:0000992",
        "label": "ovary"
    }
}

variant_entry = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
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
