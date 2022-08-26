import jsons
import boto3
import json
import pyorc
import os

from smart_open import open as sopen

from .common import AthenaModel


METADATA_BUCKET = os.environ['METADATA_BUCKET']
INDIVIDUALS_TABLE = os.environ['INDIVIDUALS_TABLE']

s3 = boto3.client('s3')
athena = boto3.client('athena')


class Individual(jsons.JsonSerializable, AthenaModel):
    _table_name = INDIVIDUALS_TABLE
    # for saving to database order matter
    _table_columns = [
        'id',
        'sampleName',
        'diseases',
        'ethnicity',
        'exposures',
        'geographicOrigin',
        'info',
        'interventionsOrProcedures',
        'karyotypicSex',
        'measures',
        'pedigrees',
        'phenotypicFeatures',
        'sex',
        'treatments'
    ]


    def __init__(
                self,
                *,
                id,
                datasetId,
                sampleName,
                diseases=[],
                ethnicity={},
                exposures=[],
                geographicOrigin={},
                info={},
                interventionsOrProcedures=[],
                karyotypicSex="",
                measures=[],
                pedigrees=[],
                phenotypicFeatures=[],
                sex={},
                treatments=[]
            ):
        self.id = id
        self.datasetId = datasetId
        self.sampleName = sampleName
        self.diseases = diseases
        self.ethnicity = ethnicity
        self.exposures = exposures
        self.geographicOrigin = geographicOrigin
        self.info = info
        self.interventionsOrProcedures = interventionsOrProcedures
        self.karyotypicSex = karyotypicSex
        self.measures = measures
        self.pedigrees = pedigrees
        self.phenotypicFeatures = phenotypicFeatures
        self.sex = sex
        self.treatments = treatments

    
    @classmethod
    def parse_array(cls, array):
        individuals = []
        var_list = list()
        case_map = { k.lower(): k for k in Individual(id='', datasetId='', sampleName='').__dict__.keys() }

        for attribute in array[0]['Data']:
            var_list.append(attribute['VarCharValue'])

        for item in array[1:]:
            individual = Individual(id='', datasetId='', sampleName='')

            for attr, val in zip(var_list, item['Data']):
                try:
                    val = json.loads(val['VarCharValue'])
                except:
                    val = val.get('VarCharValue', '')
                individual.__dict__[case_map[attr]] = val
            individuals.append(individual)

        return individuals


    @classmethod
    def upload_array(cls, array):
        header = 'struct<' + ','.join([f'{col.lower()}:string' for col in cls._table_columns]) + '>'
        partition = f'datasetid={array[0].datasetId}'
        key = f'{array[0].datasetId}-individuals'
        
        with sopen(f's3://{METADATA_BUCKET}/individuals/{partition}/{key}', 'wb') as s3file:
            with pyorc.Writer(
                s3file, 
                header, 
                compression=pyorc.CompressionKind.SNAPPY, 
                compression_strategy=pyorc.CompressionStrategy.COMPRESSION,
                bloom_filter_columns=[c.lower() for c in cls._table_columns[2:]]) as writer:
                for individual in array:
                    row = tuple(
                        individual.__dict__[k] 
                        if type(individual.__dict__[k]) == str
                        else json.dumps(individual.__dict__[k])
                        for k in cls._table_columns
                    )
                    writer.write(row)


if __name__ == '__main__':
    pass
