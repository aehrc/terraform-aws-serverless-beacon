import jsons
import boto3
import json
import pyorc
import os

from smart_open import open as sopen

from .common import AthenaModel, extract_terms


METADATA_BUCKET = os.environ['METADATA_BUCKET']
DATASETS_TABLE = os.environ['DATASETS_TABLE']

s3 = boto3.client('s3')
athena = boto3.client('athena')


class Dataset(jsons.JsonSerializable, AthenaModel):
    _table_name = DATASETS_TABLE
    # for saving to database order matter
    _table_columns = [
        'id',
        '_assemblyId',
        '_vcfLocations',
        '_vcfChromosomeMap',
        'createDateTime',
        'dataUseConditions',
        'description',
        'externalUrl',
        'info',
        'name',
        'updateDateTime',
        'version'
    ]


    def __init__(
                self,
                *,
                id='',
                assemblyId='',
                vcfLocations='',
                vcfChromosomeMap='',
                createDateTime='',
                dataUseConditions={},
                description='',
                externalUrl='',
                info={},
                name='',
                updateDateTime='',
                version=''
            ):
        self.id = id
        self._assemblyId = assemblyId
        self._vcfLocations = vcfLocations
        self._vcfChromosomeMap = vcfChromosomeMap
        self.createDateTime = createDateTime
        self.dataUseConditions = dataUseConditions
        self.description = description
        self.externalUrl = externalUrl
        self.info = info
        self.name = name
        self.updateDateTime = updateDateTime
        self.version = version
        

    def __eq__(self, other):
        return self.id == other.id


    @classmethod
    def upload_array(cls, array):
        if len(array) == 0:
            return
        header = 'struct<' + ','.join([f'{col.lower()}:string' for col in cls._table_columns]) + '>'
        bloom_filter_columns = list(map(lambda x: x.lower(), cls._table_columns))
        key = f'{array[0].id}-datasets'
        
        with sopen(f's3://{METADATA_BUCKET}/datasets/{key}', 'wb') as s3file:
            with pyorc.Writer(
                s3file, 
                header, 
                compression=pyorc.CompressionKind.SNAPPY, 
                compression_strategy=pyorc.CompressionStrategy.COMPRESSION,
                bloom_filter_columns=bloom_filter_columns) as writer:
                for dataset in array:
                    row = tuple(
                        dataset.__dict__[k] 
                        if type(dataset.__dict__[k]) == str
                        else json.dumps(dataset.__dict__[k])
                        for k in cls._table_columns
                    )
                    writer.write(row)
        
        header = 'struct<kind:string,id:string,term:string,label:string,type:string>'
        with sopen(f's3://{METADATA_BUCKET}/terms-cache/datasets-{key}', 'wb') as s3file:
            with pyorc.Writer(
                s3file, 
                header, 
                compression=pyorc.CompressionKind.SNAPPY, 
                compression_strategy=pyorc.CompressionStrategy.COMPRESSION) as writer:
                
                for dataset in array:
                    for term, label, typ in extract_terms([jsons.dump(dataset)]):
                        row = ('datasets', dataset.id, term, label, typ)
                        writer.write(row)


def get_datasets(assembly_id, dataset_id=None, dataset_ids=None, skip=0, limit=100):
    if dataset_id:
        query = f"""
            SELECT id, _vcflocations, _vcfchromosomemap 
            FROM "{{database}}"."{{table}}" 
            WHERE _assemblyid='{assembly_id}' 
            AND id='{dataset_id}'
            LIMIT 1
        """
    elif dataset_ids:
        query = f"""
            SELECT id, _vcflocations, _vcfchromosomemap 
            FROM "{{database}}"."{{table}}" 
            WHERE _assemblyid='{assembly_id}' 
            AND id IN ({','.join([f"'{id}'" for id in dataset_ids])})
            ORDER BY id 
            OFFSET {skip} 
            LIMIT {limit};
        """
    else:
        query = f"""
            SELECT id, _vcflocations, _vcfchromosomemap 
            FROM "{{database}}"."{{table}}" 
            WHERE _assemblyid='{assembly_id}' 
            ORDER BY id 
            OFFSET {skip} 
            LIMIT {limit};
        """
    return Dataset.get_by_query(query)


if __name__ == '__main__':
    pass
