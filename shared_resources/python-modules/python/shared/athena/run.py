import json
from collections import defaultdict

import jsons
import boto3
import pyorc
from smart_open import open as sopen

from .common import AthenaModel, extract_terms
from shared.utils import ENV_ATHENA


s3 = boto3.client("s3")
athena = boto3.client("athena")


class Run(jsons.JsonSerializable, AthenaModel):
    _table_name = ENV_ATHENA.ATHENA_RUNS_TABLE
    # for saving to database order matter
    _table_columns = [
        "id",
        "_datasetId",
        "_cohortId",
        "biosampleId",
        "individualId",
        "info",
        "libraryLayout",
        "librarySelection",
        "librarySource",
        "libraryStrategy",
        "platform",
        "platformModel",
        "runDate",
    ]
    _table_column_types = defaultdict(lambda: "string")

    def __init__(
        self,
        *,
        id="",
        datasetId="",
        cohortId="",
        biosampleId="",
        individualId="",
        info={},
        libraryLayout="",
        librarySelection="",
        librarySource="",
        libraryStrategy="",
        platform="",
        platformModel="",
        runDate="",
    ):
        self.id = id
        self._datasetId = datasetId
        self._cohortId = cohortId
        self.biosampleId = biosampleId
        self.individualId = individualId
        self.info = info
        self.libraryLayout = libraryLayout
        self.librarySelection = librarySelection
        self.librarySource = librarySource
        self.libraryStrategy = libraryStrategy
        self.platform = platform
        self.platformModel = platformModel
        self.runDate = runDate

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
        key = f"{array[0]['datasetId']}-runs"

        with sopen(
            f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/runs-cache/{key}", "wb"
        ) as s3file_entity, sopen(
            f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/terms-cache/runs-{key}", "wb"
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
                for run in array:
                    row = tuple(
                        run.get(k, "")
                        if type(run.get(k, "")) == str
                        else json.dumps(run.get(k, ""))
                        for k in [k.strip("_") for k in cls._table_columns]
                    )
                    writer_entity.write(row)
                    for term, label, typ in extract_terms([jsons.dump(run)]):
                        row = ("runs", run["id"], term, label, typ)
                        writer_terms.write(row)


if __name__ == "__main__":
    pass
