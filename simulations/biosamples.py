import random
import json
import os

from tqdm import tqdm
import pyorc
from smart_open import open as sopen

from athena.biosample import Biosample 
from dynamodb.datasets import Dataset
from utils import get_samples


METADATA_BUCKET = os.environ['METADATA_BUCKET']


def get_radnom_biosample(id, datasetId, individualId, seed=0):
    random.seed(seed)

    item = Biosample(id=id, datasetId=datasetId, cohortId=datasetId, individualId=individualId)
    item.biosampleStatus = random.choice([
        {
            "id": "EFO:0009654",
            "label": "reference sample"
        },
        {
            "id": "EFO:0009655",
            "label": "abnormal sample"
        },
        {
            "id": "EFO:0009656",
            "label": "neoplastic sample"
        },
        {
            "id": "EFO:0010941",
            "label": "metastasis sample"
        },
        {
            "id": "EFO:0010942",
            "label": "primary tumor sample"
        },
        {
            "id": "EFO:0010943",
            "label": "recurrent tumor sample"
        }
    ])
    item.collectionDate = random.choice([
        "2021-04-23",
        "2022-04-23",
        "2019-04-23",
        "2018-04-23",
        "2015-04-23"
    ])
    item.collectionMoment = random.choice([
        "P32Y6M1D",
        "P7D"
    ])
    item.diagnosticMarkers = []
    item.histologicalDiagnosis = random.choice([
        {},
        {
            "id": "NCIT:C3778",
            "label": "Serous Cystadenocarcinoma"
        }
    ])
    item.measurements = []
    item.obtentionProcedure = random.choice([
        {},
        {
            "code": {
                "id": "NCIT:C15189",
                "label": "biopsy"
            }
        },
        {
            "code": {
                "id": "NCIT:C157179",
                "label": "FGFR1 Mutation Analysis"
            }
        }])
    item.pathologicalStage = random.choice([
        {},
        {},
        {
            "id": "NCIT:C27977",
            "label": "Stage IIIA"
        }
    ])
    item.pathologicalTnmFinding = random.choice([
        {},
        {
            "id": "NCIT:C48725",
            "label": "T2a Stage Finding"
        },
        {
            "id": "NCIT:C48709",
            "label": "N1c Stage Finding"
        },
        {
            "id": "NCIT:C48699",
            "label": "M0 Stage Finding"
        }])
    item.phenotypicFeatures = []
    item.sampleOriginDetail = random.choice([
        {},
        {
            "id": "UBERON:0000474",
            "label": "female reproductive system"
        },
        {
            "id": "BTO:0002181",
            "label": "HEK-293T cell"
        },
        {
            "id": "OBI:0002606",
            "label": "nasopharyngeal swab specimen"
        }
    ])
    item.sampleOriginType = random.choice([
        {},
        {
            "id": "OBI:0001479",
            "label": "specimen from organism"
        },
        {
            "id": "OBI:0001876",
            "label": "cell culture"
        },
        {
            "id": "OBI:0100058",
            "label": "xenograft"
        }
    ])
    item.sampleProcessing = random.choice([
        {},
        {
            "id": "EFO:0009129",
            "label": "mechanical dissociation"
        }
    ])
    item.sampleStorage = {},
    item.tumorGrade = random.choice([
        {},
        {
            "id": "NCIT:C28080",
            "label": "Grade 3a"
        }
    ])
    item.tumorProgression = random.choice([
        {},
        {
            "id": "NCIT:C84509",
            "label": "Primary Malignant Neoplasm"
        },
        {
            "id": "NCIT:C4813",
            "label": "Recurrent Malignant Neoplasm"
        }
    ])
    item.info = []
    item.notes = []

    return item


if __name__ == "__main__":
    header = 'struct<' + ','.join([f'{col.lower()}:string' for col in Biosample._table_columns]) + '>'
    bloom_filter_columns = list(
        map(lambda x: x.lower(), Biosample._table_columns))
    # simlating 1 biosample per individual
    for dataset in Dataset.scan():
        s3file = None
        writer = None
        id = dataset.id
        nosamples = dataset.sampleCount
        vcf = list(dataset.vcfLocations)[0]
        samples = get_samples(vcf)

        for itr in tqdm(range(nosamples), total=nosamples):
            biosample = get_radnom_biosample(id=f'{id}-{itr}', datasetId=id, individualId=f'{id}-{itr}', seed=f'{id}-{itr}')
            d_partition = f'datasetid={biosample.datasetId}'
            c_partition = f'cohortid={biosample.cohortId}'
            key = f'{biosample.datasetId}-biosamples'

            if writer is None:
                s3file = sopen(f's3://{METADATA_BUCKET}/biosamples/{d_partition}/{c_partition}/{key}', 'wb')
                writer = pyorc.Writer(
                    s3file, 
                    header, 
                    compression=pyorc.CompressionKind.SNAPPY, 
                    compression_strategy=pyorc.CompressionStrategy.COMPRESSION,
                    bloom_filter_columns=bloom_filter_columns
                )
            row = tuple(
                        biosample.__dict__[k] 
                        if type(biosample.__dict__[k]) == str
                        else json.dumps(biosample.__dict__[k])
                        for k in Biosample._table_columns
                    )
            writer.write(row)
        writer.close()
        s3file.close()

    # 1 million individuals' biosamples
    s3file = None
    writer = None
    id = '1M-people-sim'
    nosamples = 10**6

    for itr in tqdm(range(nosamples)):
        biosample = get_radnom_biosample(id=f'{id}-{itr}', datasetId=id, individualId=f'{id}-{itr}', seed=f'{id}-{itr}')
        d_partition = f'datasetid={biosample.datasetId}'
        c_partition = f'cohortid={biosample.cohortId}'
        key = f'{biosample.datasetId}-biosamples'

        if writer is None:
            s3file = sopen(f's3://{METADATA_BUCKET}/biosamples/{d_partition}/{c_partition}/{key}', 'wb')
            writer = pyorc.Writer(
                s3file, 
                header, 
                compression=pyorc.CompressionKind.SNAPPY, 
                compression_strategy=pyorc.CompressionStrategy.COMPRESSION,
                bloom_filter_columns=bloom_filter_columns
            )
        row = tuple(
                    biosample.__dict__[k] 
                    if type(biosample.__dict__[k]) == str
                    else json.dumps(biosample.__dict__[k])
                    for k in Biosample._table_columns
                )
        writer.write(row)
    writer.close()
    s3file.close()

