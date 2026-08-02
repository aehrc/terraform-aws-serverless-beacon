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


class Sample(jsons.JsonSerializable, AthenaModel):
    _table_name = ENV_ATHENA.ATHENA_SAMPLES_TABLE
    # for saving to database order matter
    _table_columns = [
        "dataset_id",
        "sample_id",
        "breed",
        "sex",
    ]
    _table_column_types = defaultdict(lambda: "string")


    def init(
        self,
        *,
        dataset_id="",
        sample_id="",
        breed="",
        sex="",
    ):
        self.dataset_id = dataset_id
        self.sample_id = sample_id
        self.breed = breed
        self.sex = sex


    def eq(self, other):
        return self.dataset_id == other.dataset_id


    @classmethod
    def upload_array(cls, array):
        if len(array) == 0:
            return
        header_entity = (
            "struct<"
            + ",".join([f"{col.lower()}:{cls._table_column_types[col]}" for col in cls._table_columns])
            + ">"
        )

        key = f"{array[0]["dataset_id"]}-samples"

        with sopen(
            f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/samples/{key}", "wb"
        ) as s3file_entity:
            with pyorc.Writer(
                s3file_entity,
                header_entity,
                compression=pyorc.CompressionKind.SNAPPY,
                compression_strategy=pyorc.CompressionStrategy.COMPRESSION,
            ) as writer_entity:
                for sample in array:
                    # Writes the current row of data
                    row = tuple(
                        entry
                        for entry in [sample[col] for col in cls._table_columns]
                    )
                    writer_entity.write(row)


if __name__ == "main":
    pass

