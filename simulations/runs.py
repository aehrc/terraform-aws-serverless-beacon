import random
import json
import os

from tqdm import tqdm
import pyorc
from smart_open import open as sopen

from athena.run import Run
from dynamodb.datasets import Dataset
from utils import get_samples


METADATA_BUCKET = os.environ['METADATA_BUCKET']


def get_radnom_run(id, datasetId, individualId, biosampleId, seed=0):
    random.seed(seed)

    item = Run(id=id, datasetId=datasetId, cohortId=datasetId, individualId=individualId, biosampleId=biosampleId)
    item.libraryLayout = "PAIRED"
    item.librarySelection = "RANDOM"
    item.librarySource = random.choice(
        [
            {
                "id": "GENEPIO:0001969",
                "label": "other library source"
            },
            {
                "id": "GENEPIO:0001966",
                "label": "genomic source"
            }
        ]
    )
    item.libraryStrategy = "WGS"
    idx = random.choice([0, 1, 2])
    item.platform = ["Illumina", "PacBio", "NanoPore"][idx]
    item.platformModel = [
        {
            "id": "OBI:0002048",
            "label": "Illumina HiSeq 3000"
        },
        {
            "id": "OBI:0002012",
            "label": "PacBio RS II"
        },
        {
            "id": "OBI:0002750",
            "label": "Oxford Nanopore MinION"
        }
    ][idx]
    item.runDate = random.choice(["2021-10-18", "2022-08-08", "2018-01-01"])

    return item


if __name__ == "__main__":
    header = 'struct<' + \
        ','.join([f'{col.lower()}:string' for col in Run._table_columns]) + '>'
    bloom_filter_columns = list(
        map(lambda x: x.lower(), Run._table_columns))
    # simlating 1 run per biosample
    for dataset in Dataset.scan():
        s3file = None
        writer = None
        id = dataset.id
        nosamples = dataset.sampleCount
        vcf = list(dataset.vcfLocations)[0]
        samples = get_samples(vcf)

        for itr in tqdm(range(nosamples), total=nosamples):
            run = get_radnom_run(
                id=f'{id}-{itr}', datasetId=id, individualId=f'{id}-{itr}', biosampleId=f'{id}-{itr}', seed=f'{id}-{itr}')
            d_partition = f'datasetid={run.datasetId}'
            c_partition = f'cohortid={run.cohortId}'
            key = f'{run.datasetId}-runs'

            if writer is None:
                s3file = sopen(
                    f's3://{METADATA_BUCKET}/runs/{d_partition}/{c_partition}/{key}', 'wb')
                writer = pyorc.Writer(
                    s3file,
                    header,
                    compression=pyorc.CompressionKind.SNAPPY,
                    compression_strategy=pyorc.CompressionStrategy.COMPRESSION,
                    bloom_filter_columns=bloom_filter_columns
                )
            row = tuple(
                run.__dict__[k]
                if type(run.__dict__[k]) == str
                else json.dumps(run.__dict__[k])
                for k in Run._table_columns
            )
            writer.write(row)
        writer.close()
        s3file.close()

    # 1 million biosample's runs
    s3file = None
    writer = None
    id = '1M-people-sim'
    nosamples = 10**6

    for itr in tqdm(range(nosamples)):
        run = get_radnom_run(
            id=f'{id}-{itr}', datasetId=id, individualId=f'{id}-{itr}', biosampleId=f'{id}-{itr}', seed=f'{id}-{itr}')
        d_partition = f'datasetid={run.datasetId}'
        c_partition = f'cohortid={run.cohortId}'
        key = f'{run.datasetId}-runs'

        if writer is None:
            s3file = sopen(
                f's3://{METADATA_BUCKET}/runs/{d_partition}/{c_partition}/{key}', 'wb')
            writer = pyorc.Writer(
                s3file,
                header,
                compression=pyorc.CompressionKind.SNAPPY,
                compression_strategy=pyorc.CompressionStrategy.COMPRESSION,
                bloom_filter_columns=bloom_filter_columns
            )
        row = tuple(
            run.__dict__[k]
            if type(run.__dict__[k]) == str
            else json.dumps(run.__dict__[k])
            for k in Run._table_columns
        )
        writer.write(row)
    writer.close()
    s3file.close()
