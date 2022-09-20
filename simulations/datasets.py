import random
import json
import os

from tqdm import tqdm
import pyorc
from smart_open import open as sopen

from athena.dataset import Dataset
from dynamodb.datasets import Dataset as DynamoDataset
from utils import get_samples


METADATA_BUCKET = os.environ['METADATA_BUCKET']


def get_radnom_dataset(id, seed=0):
    random.seed(seed)

    item = Dataset(id=id)
    item.createDateTime = random.choice([
        "1999-08-05T17:21:00+01:00",
        "2002-05-21T02:37:00-08:00",
        "2019-11-21T02:37:00-08:00",
        "2020-02-21T02:37:00-08:00",
        "2021-03-21T02:37:00-08:00",
        "2022-10-21T02:37:00-08:00"
    ])
    item.dataUseConditions = random.choice([
        {
            "duoDataUse": [
                {
                    "id": "DUO:0000007",
                    "label": "disease specific research",
                    "modifiers": [
                        {
                            "id": "EFO:0001645",
                            "label": "coronary artery disease"
                        }
                    ],
                    "version": "17-07-2016"
                }
            ]
        },
        {
            "duoDataUse": [
                {
                    "id": "DUO:0000004",
                    "label": "no restriction",
                    "version": "2022-03-23"
                }
            ]
        }
    ])
    item.description = random.choice([
        "Simulation set 0.",
        "Simulation set 1.",
        "Simulation set 2.",
        "Simulation set 3."
    ])
    item.externalUrl = random.choice([
        "http://example.org/wiki/Main_Page",
        "http://example.com/vcf/vcfs",
        "http://example.net/var/variants",
        "http://example.io/data/data"
    ])
    item.info = {}
    item.name = random.choice([
        "Dataset with synthetic data",
        "Dataset with simulated data",
        "Dataset with fake data",
    ])
    item.updateDateTime = random.choice([
        "2022-08-05T17:21:00+01:00",
        "2021-09-21T02:37:00-08:00"
    ])
    item.version = random.choice([
         "v1.1",
         "v2.1",
         "v3.1",
    ])

    dynamo_item = DynamoDataset(id)
    dynamo_item.assemblyId = random.choice(["GRCH38", "GRCH37", "HG16"])
    dynamo_item.vcfGroups = []
    dynamo_item.vcfLocations = []
    dynamo_item.vcfChromosomeMap = [] 

    return item


if __name__ == "__main__":
    header = 'struct<' + \
        ','.join([f'{col.lower()}:string' for col in Dataset._table_columns]) + '>'
    bloom_filter_columns = list(
        map(lambda x: x.lower(), Dataset._table_columns))
    # simlating 1 dataset per run
    for dataset in DynamoDataset.scan():
        s3file = None
        writer = None
        id = dataset.id
        nosamples = dataset.sampleCount
        vcf = list(dataset.vcfLocations)[0]
        samples = get_samples(vcf)

        for itr, sample in tqdm(zip(range(nosamples), samples), total=nosamples):
            dataset = get_radnom_dataset(
                id=f'{id}-{itr}', datasetId=id, individualId=f'{id}-{itr}', biosampleId=f'{id}-{itr}', runId=f'{id}-{itr}', seed=f'{id}-{itr}')
            dataset.vcfSampleId = sample
            d_partition = f'datasetid={dataset.datasetId}'
            c_partition = f'cohortid={dataset.cohortId}'
            key = f'{dataset.datasetId}-analyses'

            if writer is None:
                s3file = sopen(
                    f's3://{METADATA_BUCKET}/analyses/{d_partition}/{c_partition}/{key}', 'wb')
                writer = pyorc.Writer(
                    s3file,
                    header,
                    compression=pyorc.CompressionKind.SNAPPY,
                    compression_strategy=pyorc.CompressionStrategy.COMPRESSION,
                    bloom_filter_columns=bloom_filter_columns
                )
            row = tuple(
                dataset.__dict__[k]
                if type(dataset.__dict__[k]) == str
                else json.dumps(dataset.__dict__[k])
                for k in Dataset._table_columns
            )
            writer.write(row)
        writer.close()
        s3file.close()

    # 1 million runs's analyses
    s3file = None
    writer = None
    id = '1M-people-sim'
    nosamples = 10**6

    for itr in tqdm(range(nosamples)):
        dataset = get_radnom_dataset(
            id=f'{id}-{itr}', datasetId=id, individualId=f'{id}-{itr}', biosampleId=f'{id}-{itr}', runId=f'{id}-{itr}', seed=f'{id}-{itr}')
        d_partition = f'datasetid={dataset.datasetId}'
        c_partition = f'cohortid={dataset.cohortId}'
        key = f'{dataset.datasetId}-analyses'

        if writer is None:
            s3file = sopen(
                f's3://{METADATA_BUCKET}/analyses/{d_partition}/{c_partition}/{key}', 'wb')
            writer = pyorc.Writer(
                s3file,
                header,
                compression=pyorc.CompressionKind.SNAPPY,
                compression_strategy=pyorc.CompressionStrategy.COMPRESSION,
                bloom_filter_columns=bloom_filter_columns
            )
        row = tuple(
            dataset.__dict__[k]
            if type(dataset.__dict__[k]) == str
            else json.dumps(dataset.__dict__[k])
            for k in Dataset._table_columns
        )
        writer.write(row)
    writer.close()
    s3file.close()
