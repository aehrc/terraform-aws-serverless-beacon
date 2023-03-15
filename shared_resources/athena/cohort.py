import jsons
import boto3
import json
import pyorc
import os

from smart_open import open as sopen

from .common import AthenaModel, extract_terms


ATHENA_METADATA_BUCKET = os.environ['ATHENA_METADATA_BUCKET']
ATHENA_COHORTS_TABLE = os.environ['ATHENA_COHORTS_TABLE']

s3 = boto3.client('s3')
athena = boto3.client('athena')


class Cohort(jsons.JsonSerializable, AthenaModel):
    _table_name = ATHENA_COHORTS_TABLE
    # for saving to database order matter
    _table_columns = [
        'id',
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
    def upload_array(cls, array):
        if len(array) == 0:
            return
        header = 'struct<' + \
            ','.join(
                [f'{col.lower()}:string' for col in cls._table_columns]) + '>'
        bloom_filter_columns = list(
            map(lambda x: x.lower(), cls._table_columns))
        key = f'{array[0].id}-cohorts'

        with sopen(f's3://{ATHENA_METADATA_BUCKET}/cohorts/{key}', 'wb') as s3file:
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

        header = 'struct<kind:string,id:string,term:string,label:string,type:string>'
        with sopen(f's3://{ATHENA_METADATA_BUCKET}/terms-cache/cohorts-{key}', 'wb') as s3file:
            with pyorc.Writer(
                    s3file,
                    header,
                    compression=pyorc.CompressionKind.SNAPPY,
                    compression_strategy=pyorc.CompressionStrategy.COMPRESSION) as writer:

                for cohort in array:
                    for term, label, typ in extract_terms([jsons.dump(cohort)]):
                        row = ('cohorts', cohort.id, term, label, typ)
                        writer.write(row)


if __name__ == '__main__':
    pass
