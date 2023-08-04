import json
from collections import defaultdict

import boto3
import jsons
import pyorc
from smart_open import open as sopen

from .common import AthenaModel, extract_terms
from shared.utils import ENV_ATHENA


s3 = boto3.client("s3")
athena = boto3.client("athena")


class Biosample(jsons.JsonSerializable, AthenaModel):
    _table_name = ENV_ATHENA.ATHENA_BIOSAMPLES_TABLE
    # for saving to database order matter
    _table_columns = [
        "id",
        "_datasetId",
        "_cohortId",
        "individualId",
        "biosampleStatus",
        "collectionDate",
        "collectionMoment",
        "diagnosticMarkers",
        "histologicalDiagnosis",
        "measurements",
        "obtentionProcedure",
        "pathologicalStage",
        "pathologicalTnmFinding",
        "phenotypicFeatures",
        "sampleOriginDetail",
        "sampleOriginType",
        "sampleProcessing",
        "sampleStorage",
        "tumorGrade",
        "tumorProgression",
        "info",
        "notes",
    ]
    _table_column_types = defaultdict(lambda: "string")

    def __init__(
        self,
        *,
        id="",
        datasetId="",
        cohortId="",
        individualId="",
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
        notes=[],
    ):
        self.id = id
        self._datasetId = datasetId
        self._cohortId = cohortId
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

    def __eq__(self, other):
        return self.id == other.id

    @classmethod
    def upload_array(cls, array):
        if len(array) == 0:
            return
        header_entity = (
            "struct<"
            + ",".join([f"{col.lower()}:string" for col in cls._table_columns])
            + ">"
        )
        header_terms = (
            "struct<kind:string,id:string,term:string,label:string,type:string>"
        )
        key = f"{array[0]['datasetId']}-biosamples"

        with sopen(
            f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/biosamples-cache/{key}", "wb"
        ) as s3file_entity, sopen(
            f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/terms-cache/biosamples-{key}",
            "wb",
        ) as s3file_terms:
            with pyorc.Writer(
                s3file_entity,
                header_entity,
                compression=pyorc.CompressionKind.SNAPPY,
                compression_strategy=pyorc.CompressionStrategy.COMPRESSION,
            ) as writer_entity, pyorc.Writer(
                s3file_terms,
                header_terms,
                compression=pyorc.CompressionKind.SNAPPY,
                compression_strategy=pyorc.CompressionStrategy.COMPRESSION,
            ) as writer_terms:
                for biosample in array:
                    row = tuple(
                        biosample.get(k, "")
                        if type(biosample.get(k, "")) == str
                        else json.dumps(biosample.get(k, ""))
                        for k in [k.strip("_") for k in cls._table_columns]
                    )
                    writer_entity.write(row)
                    for term, label, typ in extract_terms([biosample]):
                        row = ("biosamples", biosample["id"], term, label, typ)
                        writer_terms.write(row)


if __name__ == "__main__":
    pass
