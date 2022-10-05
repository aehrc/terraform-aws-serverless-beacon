import jsons
import boto3
import json
import pyorc
import os

from smart_open import open as sopen

from .common import AthenaModel


METADATA_BUCKET = os.environ['METADATA_BUCKET']
ANALYSES_TABLE = os.environ['ANALYSES_TABLE']

s3 = boto3.client('s3')
athena = boto3.client('athena')


class Analysis(jsons.JsonSerializable, AthenaModel):
    _table_name = ANALYSES_TABLE
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
    def parse_array(cls, array):
        analyses = []
        var_list = list()
        # TODO
        case_map = { k.lower(): k for k in Analysis().__dict__.keys() }

        for attribute in array[0]['Data']:
            var_list.append(attribute['VarCharValue'])

        for item in array[1:]:
            analysis = Analysis()

            for attr, val in zip(var_list, item['Data']):
                try:
                    val = json.loads(val['VarCharValue'])
                except:
                    val = val.get('VarCharValue', '')
                analysis.__dict__[case_map[attr]] = val
            analyses.append(analysis)

        return analyses


    @classmethod
    def upload_array(cls, array):
        if len(array) == 0:
            return
        header = 'struct<' + ','.join([f'{col.lower()}:string' for col in cls._table_columns]) + '>'
        bloom_filter_columns = [c.lower() for c in cls._table_columns]
        d_partition = f'datasetid={array[0].datasetId}'
        c_partition = f'cohortid={array[0].cohortId}'
        key = f'{array[0].datasetId}-analyses'
        
        with sopen(f's3://{METADATA_BUCKET}/analyses/{d_partition}/{c_partition}/{key}', 'wb') as s3file:
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


if __name__ == '__main__':
    pass
