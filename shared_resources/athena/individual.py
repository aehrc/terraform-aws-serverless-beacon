from typing import List
import jsons
import boto3
import json


s3 = boto3.client('s3')
athena = boto3.client('athena')


class Individual(jsons.JsonSerializable):
    # for saving to database order matter
    table_columns = [
        'id',
        'samplename',
        'diseases',
        'ethnicity',
        'exposures',
        'geographicorigin',
        'info',
        'interventionsorprocedures',
        'karyotypicsex',
        'measures',
        'pedigrees',
        'phenotypicfeatures',
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
                    pass
                individual.__dict__[case_map[attr]] = val
            individuals.append(individual)

        return individuals


    @classmethod
    def upload_array(cls, array):
        table = { k: [] for k in cls.table_columns }
        for individual in array:
            for k, v in individual.dump().items():
                k = k.lower()
                if k == 'datasetid':
                    continue
                if isinstance(v, str):
                    table[k].append(v)
                else:
                    table[k].append(json.dumps(v))
        
        # table = pa.table(table)

if __name__ == '__main__':
    pass
