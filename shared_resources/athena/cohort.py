import jsons
import boto3
import json
import pyorc
import os

from smart_open import open as sopen

from .common import AthenaModel


METADATA_BUCKET = os.environ['METADATA_BUCKET']
COHORTS_TABLE = os.environ['COHORTS_TABLE']

s3 = boto3.client('s3')
athena = boto3.client('athena')


class Cohort(jsons.JsonSerializable, AthenaModel):
    _table_name = COHORTS_TABLE
    # for saving to database order matter
    _table_columns = [
        'cohortDataTypes',
        'cohortDesign',
        'cohortSize',
        'cohortType',
        'collectionEvents',
        'exclusionCriteria',
        'inclusionCriteria',
        'name'
    ]


    def __init__(
                self,
                *,
                id='',
                cohortDataTypes='',
                cohortDesign='',
                cohortSize='',
                cohortType='',
                collectionEvents='',
                exclusionCriteria='',
                inclusionCriteria='',
                name=''
            ):
        self.id = id
        self.cohortDataTypes = cohortDataTypes
        self.cohortDesign = cohortDesign
        self.cohortSize = cohortSize
        self.cohortType = cohortType
        self.collectionEvents = collectionEvents
        self.exclusionCriteria = exclusionCriteria
        self.inclusionCriteria = inclusionCriteria
        self.name = name
        


    def __eq__(self, other):
        return self.id == other.id


    @classmethod
    def parse_array(cls, array):
        cohorts = []
        var_list = list()
        case_map = { k.lower(): k for k in Cohort().__dict__.keys() }

        for attribute in array[0]['Data']:
            var_list.append(attribute['VarCharValue'])

        for item in array[1:]:
            cohort = Cohort()

            for attr, val in zip(var_list, item['Data']):
                try:
                    val = json.loads(val['VarCharValue'])
                except:
                    val = val.get('VarCharValue', '')
                cohort.__dict__[case_map[attr]] = val
            cohorts.append(cohort)

        return cohorts


    @classmethod
    def upload_array(cls, array):
        if len(array) == 0:
            return
        header = 'struct<' + ','.join([f'{col.lower()}:string' for col in cls._table_columns]) + '>'
        bloom_filter_columns = list(map(lambda x: x.lower(), cls._table_columns))
        partition = f'id={array[0].id}'
        key = f'{array[0].id}-cohorts'
        
        with sopen(f's3://{METADATA_BUCKET}/cohorts/{partition}/{key}', 'wb') as s3file:
            with pyorc.Writer(
                s3file, 
                header, 
                compression=pyorc.CompressionKind.SNAPPY, 
                compression_strategy=pyorc.CompressionStrategy.COMPRESSION,
                bloom_filter_columns=bloom_filter_columns) as writer:
                for cohort in array:
                    row = tuple(
                        cohort.__dict__[k] 
                        if type(cohort.__dict__[k]) == str
                        else json.dumps(cohort.__dict__[k])
                        for k in cls._table_columns
                    )
                    writer.write(row)


if __name__ == '__main__':
    pass
