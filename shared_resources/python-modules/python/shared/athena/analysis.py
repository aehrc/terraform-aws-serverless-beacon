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


class Analysis(jsons.JsonSerializable, AthenaModel):
    _table_name = ENV_ATHENA.ATHENA_ANALYSES_TABLE
    # for saving to database order matter
    _table_columns = [
        "id",
        "_datasetId",
        "_cohortId",
        "_vcfSampleId",
        "individualId",
        "biosampleId",
        "runId",
        "aligner",
        "analysisDate",
        "info",
        "pipelineName",
        "pipelineRef",
        "variantCaller",
    ]
    _table_column_types = defaultdict(lambda: "string")

    def __init__(
        self,
        *,
        id="",
        datasetId="",
        cohortId="",
        individualId="",
        biosampleId="",
        runId="",
        aligner="",
        analysisDate="",
        info={},
        pipelineName="",
        pipelineRef="",
        variantCaller="",
        vcfSampleId="",
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
        header_entity = (
            "struct<"
            + ",".join([f"{col.lower()}:string" for col in cls._table_columns])
            + ">"
        )
        header_terms = (
            "struct<kind:string,id:string,term:string,label:string,type:string>"
        )
        key = f"{array[0]['datasetId']}-analyses"

        with sopen(
            f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/analyses-cache/{key}", "wb"
        ) as s3file_entity, sopen(
            f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/terms-cache/analyses-{key}", "wb"
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
                for analysis in array:
                    row = tuple(
                        analysis.get(k, "")
                        if type(analysis.get(k, "")) == str
                        else json.dumps(analysis.get(k, ""))
                        for k in [k.strip("_") for k in cls._table_columns]
                    )
                    writer_entity.write(row)
                    for term, label, typ in extract_terms([jsons.dump(analysis)]):
                        row = ("analyses", analysis["id"], term, label, typ)
                        writer_terms.write(row)


if __name__ == "__main__":
    pass
