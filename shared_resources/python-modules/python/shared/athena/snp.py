import json
from collections import defaultdict

import jsons
import boto3
import pyorc
from smart_open import open as sopen

from .common import AthenaModel
from shared.utils import ENV_ATHENA


s3 = boto3.client("s3")
athena = boto3.client("athena")


class Snp(jsons.JsonSerializable, AthenaModel):
    _table_name = ENV_ATHENA.ATHENA_SNPS_TABLE
    # for saving to database order matter
    _table_columns = [
        "dataset_id",
        "id",
        "chromosome",
        "coordinate",
        "allelea_top_base",
        "alleleb_top_base"
    ]
    _table_column_types = defaultdict(lambda: "string", {"coordinate": "double"})


    def init(
        self,
        *,
        dataset_id="",
        id="",
        chromosome="",
        coordinate="",
        allelea_top_base="",
        alleleb_top_base="",
    ):
        self.dataset_id = dataset_id
        self.id = id
        self.chromosome = chromosome
        self.coordinate = coordinate
        self.allelea_top_base = allelea_top_base
        self.alleleb_top_base = alleleb_top_base


    def eq(self, other):
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

        key = f"{array[0]["dataset_id"]}-snps"

        with sopen(
            f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/snps/{key}", "wb"
        ) as s3file_entity:
            with pyorc.Writer(
                s3file_entity,
                header_entity,
                compression=pyorc.CompressionKind.SNAPPY,
                compression_strategy=pyorc.CompressionStrategy.COMPRESSION,
            ) as writer_entity:
                for snp in array:
                    # Writes the current row of data
                    row = tuple(
                        entry
                        for entry in [snp[col] for col in cls._table_columns]
                    )
                    writer_entity.write(row)


if __name__ == "main":
    pass

