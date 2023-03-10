import jsons
import boto3
import json
import pyorc
import os

from smart_open import open as sopen

from .common import AthenaModel, extract_terms


ATHENA_METADATA_BUCKET = os.environ['ATHENA_METADATA_BUCKET']
ATHENA_RUNS_TABLE = os.environ['ATHENA_RUNS_TABLE']

s3 = boto3.client('s3')
athena = boto3.client('athena')


class Run(jsons.JsonSerializable, AthenaModel):
    _table_name = ATHENA_RUNS_TABLE
    # for saving to database order matter
    _table_columns = [
        'id',
        '_datasetId',
        '_cohortId',
        'biosampleId',
        'individualId',
        'info',
        'libraryLayout',
        'librarySelection',
        'librarySource',
        'libraryStrategy',
        'platform',
        'platformModel',
        'runDate'
    ]

    def __init__(
        self,
        *,
        id='',
        datasetId='',
        cohortId='',
        biosampleId='',
        individualId='',
        info={},
        libraryLayout='',
        librarySelection='',
        librarySource='',
        libraryStrategy='',
        platform='',
        platformModel='',
        runDate=''
    ):
        self.id = id
        self._datasetId = datasetId
        self._cohortId = cohortId
        self.biosampleId = biosampleId
        self.individualId = individualId
        self.info = info
        self.libraryLayout = libraryLayout
        self.librarySelection = librarySelection
        self.librarySource = librarySource
        self.libraryStrategy = libraryStrategy
        self.platform = platform
        self.platformModel = platformModel
        self.runDate = runDate

    def __eq__(self, other):
        return self.id == other.id

    @classmethod
    def upload_array(cls, array):
        if len(array) == 0:
            return
        header = 'struct<' + \
            ','.join(
                [f'{col.lower()}:string' for col in cls._table_columns]) + '>'
        bloom_filter_columns = [c.lower() for c in cls._table_columns]
        key = f'{array[0]._datasetId}-runs'

        with sopen(f's3://{ATHENA_METADATA_BUCKET}/runs/{key}', 'wb') as s3file:
            with pyorc.Writer(
                    s3file,
                    header,
                    compression=pyorc.CompressionKind.SNAPPY,
                    compression_strategy=pyorc.CompressionStrategy.COMPRESSION,
                    bloom_filter_columns=bloom_filter_columns) as writer:
                for run in array:
                    row = tuple(
                        run.__dict__[k]
                        if type(run.__dict__[k]) == str
                        else json.dumps(run.__dict__[k])
                        for k in cls._table_columns
                    )
                    writer.write(row)

        header = 'struct<kind:string,id:string,term:string,label:string,type:string>'
        with sopen(f's3://{ATHENA_METADATA_BUCKET}/terms-cache/runs-{key}', 'wb') as s3file:
            with pyorc.Writer(
                    s3file,
                    header,
                    compression=pyorc.CompressionKind.SNAPPY,
                    compression_strategy=pyorc.CompressionStrategy.COMPRESSION) as writer:

                for run in array:
                    for term, label, typ in extract_terms([jsons.dump(run)]):
                        row = ('runs', run.id, term, label, typ)
                        writer.write(row)


if __name__ == '__main__':
    pass
