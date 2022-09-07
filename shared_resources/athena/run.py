import jsons
import boto3
import json
import pyorc
import os

from smart_open import open as sopen

from .common import AthenaModel


METADATA_BUCKET = os.environ['METADATA_BUCKET']
RUNS_TABLE = os.environ['INDIVIDUALS_TABLE']

s3 = boto3.client('s3')
athena = boto3.client('athena')


class Run(jsons.JsonSerializable, AthenaModel):
    _table_name = RUNS_TABLE
    # for saving to database order matter
    _table_columns = [
        'id',
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
        self.datasetId = datasetId
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
    def parse_array(cls, array):
        runs = []
        var_list = list()
        # TODO
        case_map = { k.lower(): k for k in Run().__dict__.keys() }

        for attribute in array[0]['Data']:
            var_list.append(attribute['VarCharValue'])

        for item in array[1:]:
            run = Run()

            for attr, val in zip(var_list, item['Data']):
                try:
                    val = json.loads(val['VarCharValue'])
                except:
                    val = val.get('VarCharValue', '')
                run.__dict__[case_map[attr]] = val
            runs.append(run)

        return runs


    @classmethod
    def upload_array(cls, array):
        if len(array) == 0:
            return
        header = 'struct<' + ','.join([f'{col.lower()}:string' for col in cls._table_columns]) + '>'
        partition = f'datasetid={array[0].datasetId}'
        key = f'{array[0].datasetId}-runs'
        
        with sopen(f's3://{METADATA_BUCKET}/runs/{partition}/{key}', 'wb') as s3file:
            with pyorc.Writer(
                s3file, 
                header, 
                compression=pyorc.CompressionKind.SNAPPY, 
                compression_strategy=pyorc.CompressionStrategy.COMPRESSION,
                bloom_filter_columns=[c.lower() for c in cls._table_columns[2:]]) as writer:
                for run in array:
                    row = tuple(
                        run.__dict__[k] 
                        if type(run.__dict__[k]) == str
                        else json.dumps(run.__dict__[k])
                        for k in cls._table_columns
                    )
                    writer.write(row)


if __name__ == '__main__':
    pass
