import jsons
import boto3
import json


s3 = boto3.client('s3')
athena = boto3.client('athena')


class Biosample(jsons.JsonSerializable):
    def __init__(
                self,
                *,
                id='',
                individualId='',
                biosampleStatus={},
                collectionDate=[],
                collectionMoment=[],
                diagnosticMarkers=[],
                histologicalDiagnosis=[],
                measurements=[],
                obtentionProcedure=[],
                pathologicalStage=[],
                pathologicalTnmFinding=[],
                phenotypicFeatures=[],
                sampleOriginDetail=[],
                sampleOriginType=[],
                sampleProcessing=[],
                sampleStorage=[],
                tumorGrade=[],
                tumorProgression=[],
                info=[],
                notes=[]
            ):
        self.id = id
        self.individualId = individualId
        self.biosampleStatus = biosampleStatus
        self.collectionDate = collectionDate
        self.collectionMoment = collectionMoment
        self.diagnosticMarkers = diagnosticMarkers
        self.histologicalDiagnosis = histologicalDiagnosis
        self.measurements = measurements
        self.obtentionProcedure = obtentionProcedure
        self.pathologicalStage = pathologicalStage
        self.pathologicalTnmFinding = pathologicalTnmFinding
        self.phenotypicFeatures = phenotypicFeatures
        self.sampleOriginDetail = sampleOriginDetail
        self.sampleOriginType = sampleOriginType
        self.sampleProcessing = sampleProcessing
        self.sampleStorage = sampleStorage
        self.tumorGrade = tumorGrade
        self.tumorProgression = tumorProgression
        self.info = info
        self.notes = notes

    
    @classmethod
    def parse_array(cls, array):
        biosamples = []
        var_list = list()
        case_map = { k.lower(): k for k in Biosample(id='', individualId='').__dict__.keys() }

        for attribute in array[0]['Data']:
            var_list.append(attribute['VarCharValue'])

        for item in array[1:]:
            biosample = Biosample(id='', individualId='')

            for attr, val in zip(var_list, item['Data']):
                try:
                    val = json.loads(val['VarCharValue'])
                except:
                    pass
                biosample.__dict__[case_map[attr]] = val
            biosamples.append(biosample)

        return biosamples


if __name__ == '__main__':
    pass
