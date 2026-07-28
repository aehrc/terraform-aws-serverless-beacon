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


class Phenotype(jsons.JsonSerializable, AthenaModel):
    _table_name = ENV_ATHENA.ATHENA_PHENOTYPES_TABLE
    # for saving to database order matter
    _table_columns = [
        "dataset_id",
        "sample_id",
        "sex",
        "birth_weight_kg",
        "weaning_weight_kg",
        "six_month_weight_kg",
        "fat_thickness_cm",
        "eye_muscle_area_cm2",
        "height_at_withers_cm",
        "chest_girth_cm",
        "shin_circumference_cm",
        "pre_weaning_gain_kg",
        "post_weaning_gain_kg",
        "daily_weight_gain_kg"
    ]
    _table_column_types = defaultdict(
        lambda: "string", 
        {
            "birth_weight_kg": "double", 
            "weaning_weight_kg": "double", 
            "six_month_weight_kg": "double", 
            "fat_thickness_cm": "double", 
            "eye_muscle_area_cm2": "double", 
            "height_at_withers_cm": "double", 
            "chest_girth_cm": "double", 
            "shin_circumference_cm": "double", 
            "pre_weaning_gain_kg": "double", 
            "post_weaning_gain_kg": "double", 
            "daily_weight_gain_kg": "double"
        }
    )


    def init(
        self,
        *,
        dataset_id="",
        sample_id="",
        sex="",
        birth_weight_kg="",
        weaning_weight_kg="",
        six_month_weight_kg="",
        fat_thickness_cm="",
        eye_muscle_area_cm2="",
        height_at_withers_cm="",
        chest_girth_cm="",
        shin_circumference_cm="",
        pre_weaning_gain_kg="",
        post_weaning_gain_kg="",
        daily_weight_gain_kg=""
    ):
        self.dataset_id = dataset_id
        self.sample_id = sample_id
        self.sex = sex
        self.birth_weight_kg = birth_weight_kg
        self.weaning_weight_kg = weaning_weight_kg
        self.six_month_weight_kg = six_month_weight_kg
        self.fat_thickness_cm = fat_thickness_cm
        self.eye_muscle_area_cm2 = eye_muscle_area_cm2
        self.height_at_withers_cm = height_at_withers_cm
        self.chest_girth_cm = chest_girth_cm
        self.shin_circumference_cm = shin_circumference_cm
        self.pre_weaning_gain_kg = pre_weaning_gain_kg
        self.post_weaning_gain_kg = post_weaning_gain_kg
        self.daily_weight_gain_kg = daily_weight_gain_kg


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

        key = f"{array[0]["dataset_id"]}-{array[0]["sample_id"]}-phenotypes"

        with sopen(
            f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/phenotypes/{key}", "wb"
        ) as s3file_entity:
            with pyorc.Writer(
                s3file_entity,
                header_entity,
                compression=pyorc.CompressionKind.SNAPPY,
                compression_strategy=pyorc.CompressionStrategy.COMPRESSION,
            ) as writer_entity:
                for phenotype in array:
                    # Writes the current row of data
                    row = tuple(
                        entry
                        for entry in [phenotype[col] for col in cls._table_columns]
                    )
                    writer_entity.write(row)


if __name__ == "main":
    pass

