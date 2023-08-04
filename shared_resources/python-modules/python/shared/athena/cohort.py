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


class Cohort(jsons.JsonSerializable, AthenaModel):
    _table_name = ENV_ATHENA.ATHENA_COHORTS_TABLE
    # for saving to database order matter
    _table_columns = [
        "id",
        "cohortDataTypes",
        "cohortDesign",
        "cohortSize",
        "cohortType",
        "collectionEvents",
        "exclusionCriteria",
        "inclusionCriteria",
        "name",
    ]
    _table_column_types = defaultdict(lambda: "string")
    _table_column_types["cohortSize"] = "int"

    def __init__(
        self,
        *,
        id="",
        cohortDataTypes="",
        cohortDesign="",
        cohortSize="",
        cohortType="",
        collectionEvents="",
        exclusionCriteria="",
        inclusionCriteria="",
        name="",
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
        header_entity = (
            "struct<"
            + ",".join([f"{col.lower()}:{cls._table_column_types[col]}" for col in cls._table_columns])
            + ">"
        )
        header_terms = (
            "struct<kind:string,id:string,term:string,label:string,type:string>"
        )
        key = f"{array[0]['id']}-cohorts"

        with sopen(
            f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/cohorts-cache/{key}", "wb"
        ) as s3file_entity, sopen(
            f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/terms-cache/cohorts-{key}", "wb"
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
                for cohort in array:
                    row = tuple(
                        cohort.get(k, "")
                        if type(cohort.get(k, "")) in (str, int)
                        else json.dumps(cohort.get(k, ""))
                        for k in [k.strip("_") for k in cls._table_columns]
                    )
                    writer_entity.write(row)
                    for term, label, typ in extract_terms([cohort]):
                        row = ("cohorts", cohort["id"], term, label, typ)
                        writer_terms.write(row)


if __name__ == "__main__":
    pass
