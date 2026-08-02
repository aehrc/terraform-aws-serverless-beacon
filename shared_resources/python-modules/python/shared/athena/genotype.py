import json
from collections import defaultdict
from datetime import datetime, timezone

import jsons
import boto3
import pyorc
from smart_open import open as sopen

from .common import AthenaModel
from shared.utils import ENV_ATHENA


s3 = boto3.client("s3")
athena = boto3.client("athena")


class Genotype(jsons.JsonSerializable, AthenaModel):
    _table_name = ENV_ATHENA.ATHENA_GENOTYPES_TABLE
    # for saving to database order matter
    _table_columns = [
        "dataset_id",
        "id_ref",
        "sample_id",
        "value",
        "score",
        "theta",
        "b_allele_freq"
    ]
    _table_column_types = defaultdict(lambda: "string", {"score": "double", "theta": "double", "b_allele_freq": "double"})


    def init(
        self,
        *,
        dataset_id="",
        id_ref="",
        sample_id="",
        value="",
        score="",
        theta="",
        b_allele_freq=""
    ):
        self.dataset_id = dataset_id
        self.id_ref = id_ref
        self.sample_id = sample_id
        self.value = value
        self.score = score
        self.theta = theta
        self.b_allele_freq = b_allele_freq


    def eq(self, other):
        return self.sample_id == other.sample_id


    @classmethod
    def upload_array(cls, array):
        if len(array) == 0:
            return
        header_entity = (
            "struct<"
            + ",".join([f"{col.lower()}:{cls._table_column_types[col]}" for col in cls._table_columns])
            + ">"
        )

        key = f"{array[0]["dataset_id"]}-{array[0]["sample_id"]}-genotypes"

        with sopen(
            f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/genotypes/{key}", "wb"
        ) as s3file_entity:
            with pyorc.Writer(
                s3file_entity,
                header_entity,
                compression=pyorc.CompressionKind.SNAPPY,
                compression_strategy=pyorc.CompressionStrategy.COMPRESSION,
            ) as writer_entity:
                for genotype in array:
                    # Writes the current row of data
                    row = tuple(
                        entry
                        for entry in [genotype[col] for col in cls._table_columns]
                    )
                    writer_entity.write(row)


if __name__ == "main":
    pass

