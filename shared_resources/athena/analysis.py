import jsons
import boto3
import json
import pyorc
import os

from smart_open import open as sopen

from .common import AthenaModel, extract_terms


ATHENA_METADATA_BUCKET = os.environ['ATHENA_METADATA_BUCKET']
ATHENA_ANALYSES_TABLE = os.environ['ATHENA_ANALYSES_TABLE']

s3 = boto3.client('s3')
athena = boto3.client('athena')


class Analysis(jsons.JsonSerializable, AthenaModel):
    _table_name = ATHENA_ANALYSES_TABLE
    # for saving to database order matter
    _table_columns = [
        'id',
        '_datasetId',
        '_cohortId',
        '_vcfSampleId',
        'individualId',
        'biosampleId',
        'runId',
        'aligner',
        'analysisDate',
        'info',
        'pipelineName',
        'pipelineRef',
        'variantCaller'
    ]


    def __init__(
                self,
                *,
                id='',
                datasetId='',
                cohortId='',
                individualId='',
                biosampleId='',
                runId='',
                aligner='',
                analysisDate='',
                info={},
                pipelineName='',
                pipelineRef='',
                variantCaller='',
                vcfSampleId=''
            ):
        self.id = id
        self._datasetId = datasetId
        self._cohortId = cohortId
        self._vcfSampleId = vcfSampleId
        self.individualId = individualId
        self.biosampleId = biosampleId
        self.runId = runId
        self.aligner = aligner
        self.analysisDate = analysisDate
        self.info = info
        self.pipelineName = pipelineName
        self.pipelineRef = pipelineRef
        self.variantCaller = variantCaller


    def __eq__(self, other):
        return self.id == other.id


    @classmethod
    def upload_array(cls, array):
        if len(array) == 0:
            return
        header = 'struct<' + ','.join([f'{col.lower()}:string' for col in cls._table_columns]) + '>'
        bloom_filter_columns = [c.lower() for c in cls._table_columns]
        key = f'{array[0]._datasetId}-analyses'
        
        with sopen(f's3://{ATHENA_METADATA_BUCKET}/analyses/{key}', 'wb') as s3file:
            with pyorc.Writer(
                s3file, 
                header, 
                compression=pyorc.CompressionKind.SNAPPY, 
                compression_strategy=pyorc.CompressionStrategy.COMPRESSION,
                bloom_filter_columns=bloom_filter_columns) as writer:
                for analysis in array:
                    row = tuple(
                        analysis.__dict__[k] 
                        if type(analysis.__dict__[k]) == str
                        else json.dumps(analysis.__dict__[k])
                        for k in cls._table_columns
                    )
                    writer.write(row)
        
        header = 'struct<kind:string,id:string,term:string,label:string,type:string>'
        with sopen(f's3://{ATHENA_METADATA_BUCKET}/terms-cache/analyses-{key}', 'wb') as s3file:
            with pyorc.Writer(
                s3file, 
                header, 
                compression=pyorc.CompressionKind.SNAPPY, 
                compression_strategy=pyorc.CompressionStrategy.COMPRESSION) as writer:
                
                for analysis in array:
                    for term, label, typ in extract_terms([jsons.dump(analysis)]):
                        row = ('analyses', analysis.id, term, label, typ)
                        writer.write(row)


if __name__ == '__main__':
    pass
