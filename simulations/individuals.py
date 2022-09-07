import random
import json
import os

from tqdm import tqdm
import pyorc
from smart_open import open as sopen

from athena.individual import Individual
from dynamodb.datasets import Dataset
from utils import get_samples


METADATA_BUCKET = os.environ['METADATA_BUCKET']


def get_radnom_individual(id, datasetId, seed=0):
    random.seed(seed)

    item= Individual(id=id, datasetId=datasetId)
    item.diseases = []
    item.ethnicity = random.choice([
        {
            "id": "NCIT:C42331",
            "label": "African"
        },
        {
            "id": "NCIT:C41260",
            "label": "Asian"
        },
        {
            "id": "NCIT:C126535",
            "label": "Australian"
        },
        {
            "id": "NCIT:C43851",
            "label": "European"
        },
        {
            "id": "NCIT:C77812",
            "label": "North American"
        },
        {
            "id": "NCIT:C126531",
            "label": "Latin American"
        },
        {
            "id": "NCIT:C104495",
            "label": "Other race"
        }
    ])
    item.exposures = []
    item.geographicOrigin = random.choice([
        {
            "id": "GAZ:00002955",
            "label": "Slovenia"
        },
        {
            "id": "GAZ:00002459",
            "label": "United States of America"
        },
        {
            "id": "GAZ:00316959",
            "label": "Municipality of El Masnou"
        },
        {
            "id": "GAZ:00000460",
            "label": "Eurasia"
        }
    ])
    item.info = {}
    item.interventionsOrProcedures = []
    item.karyotypicSex = random.choice([
        "UNKNOWN_KARYOTYPE",
        "XX",
        "XY",
        "XO",
        "XXY",
        "XXX",
        "XXYY",
        "XXXY",
        "XXXX",
        "XYY",
        "OTHER_KARYOTYPE"
    ])
    item.measures = []
    item.pedigrees = []
    item.phenotypicFeatures = []
    item.sex = random.choice([
        {
            "id": "NCIT:C16576",
            "label": "female"
        },
        {
            "id": "NCIT:C20197",
            "label": "male"
        },
        {
            "id": "NCIT:C1799",
            "label": "unknown"
        }
    ])
    item.treatments = []

    return item


if __name__ == "__main__":
    # simlating 1 person per vcf sample
    header = 'struct<' + \
        ','.join(
            [f'{col.lower()}:string' for col in Individual._table_columns]) + '>'
    bloom_filter_columns = list(
        map(lambda x: x.lower(), Individual._table_columns))
    

    for dataset in Dataset.scan():
        s3file = None
        writer = None
        id = dataset.id
        nosamples = dataset.sampleCount
        vcf = list(dataset.vcfLocations)[0]
        samples = get_samples(vcf)

        for itr in tqdm(zip(nosamples), total=nosamples):
            individual = get_radnom_individual(
                id=f'{id}-{itr}', datasetId=id, seed=f'{id}-{itr}')
            partition = f'datasetid={individual.datasetId}'
            key = f'{individual.datasetId}-individuals'

            if writer is None:
                s3file = sopen(
                    f's3://{METADATA_BUCKET}/individuals/{partition}/{key}', 'wb')

                writer = pyorc.Writer(
                    s3file,
                    header,
                    compression=pyorc.CompressionKind.SNAPPY,
                    compression_strategy=pyorc.CompressionStrategy.COMPRESSION,
                    bloom_filter_columns=bloom_filter_columns
                )
            row = tuple(
                individual.__dict__[k]
                if type(individual.__dict__[k]) == str
                else json.dumps(individual.__dict__[k])
                for k in Individual._table_columns
            )
            writer.write(row)
        writer.close()
        s3file.close()

    # simulating dummy 1M people
    s3file = None
    writer = None
    id = '1M-people-sim'
    nosamples = 10**6

    for itr in tqdm(range(nosamples)):
        sample = 'NA'
        individual = get_radnom_individual(
            id=f'{id}-{itr}', datasetId=id, seed=f'{id}-{itr}')
        partition = f'datasetid={individual.datasetId}'
        key = f'{individual.datasetId}-individuals'

        if writer is None:
            s3file = sopen(
                f's3://{METADATA_BUCKET}/individuals/{partition}/{key}', 'wb')
            writer = pyorc.Writer(
                s3file,
                header,
                compression=pyorc.CompressionKind.SNAPPY,
                compression_strategy=pyorc.CompressionStrategy.COMPRESSION,
                bloom_filter_columns=bloom_filter_columns
            )
        row = tuple(
            individual.__dict__[k]
            if type(individual.__dict__[k]) == str
            else json.dumps(individual.__dict__[k])
            for k in Individual._table_columns
        )
        writer.write(row)
    writer.close()
    s3file.close()
