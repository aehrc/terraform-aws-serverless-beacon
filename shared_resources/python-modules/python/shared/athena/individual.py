import json
from collections import defaultdict

import pyorc
import jsons
import boto3
from smart_open import open as sopen

from .common import AthenaModel, extract_terms
from shared.utils import ENV_ATHENA


s3 = boto3.client("s3")
athena = boto3.client("athena")


class Individual(jsons.JsonSerializable, AthenaModel):
    _table_name = ENV_ATHENA.ATHENA_INDIVIDUALS_TABLE
    # for saving to database order matter
    _table_columns = [
        "id",
        "_datasetId",
        "_cohortId",
        "diseases",
        "ethnicity",
        "exposures",
        "geographicOrigin",
        "info",
        "interventionsOrProcedures",
        "karyotypicSex",
        "measures",
        "pedigrees",
        "phenotypicFeatures",
        "sex",
        "treatments",
    ]
    _table_column_types = defaultdict(lambda: "string")

    def __init__(
        self,
        *,
        id="",
        datasetId="",
        cohortId="",
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
        treatments=[],
    ):
        self.id = id
        self._datasetId = datasetId
        self._cohortId = cohortId
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
        key = f"{array[0]['datasetId']}-individuals"

        with sopen(
            f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/individuals-cache/{key}", "wb"
        ) as s3file_entity, sopen(
            f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/terms-cache/individuals-{key}",
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
                for individual in array:
                    row = tuple(
                        individual.get(k, "")
                        if type(individual.get(k, "")) == str
                        else json.dumps(individual.get(k, ""))
                        for k in [k.strip("_") for k in cls._table_columns]
                    )
                    writer_entity.write(row)
                    for term, label, typ in extract_terms([jsons.dump(individual)]):
                        row = ("individuals", individual["id"], term, label, typ)
                        writer_terms.write(row)


if __name__ == "__main__":
    pass
