import json
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
        header = (
            "struct<"
            + ",".join([f"{col.lower()}:string" for col in cls._table_columns])
            + ">"
        )
        bloom_filter_columns = list(map(lambda x: x.lower(), cls._table_columns))
        key = f"{array[0]._datasetId}-individuals"

        with sopen(f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/individuals/{key}", "wb") as s3file:
            with pyorc.Writer(
                s3file,
                header,
                compression=pyorc.CompressionKind.SNAPPY,
                compression_strategy=pyorc.CompressionStrategy.COMPRESSION,
                bloom_filter_columns=bloom_filter_columns,
            ) as writer:
                for individual in array:
                    row = tuple(
                        individual.__dict__[k]
                        if type(individual.__dict__[k]) == str
                        else json.dumps(individual.__dict__[k])
                        for k in cls._table_columns
                    )
                    writer.write(row)

        header = "struct<kind:string,id:string,term:string,label:string,type:string>"
        with sopen(
            f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/terms-cache/individuals-{key}", "wb"
        ) as s3file:
            with pyorc.Writer(
                s3file,
                header,
                compression=pyorc.CompressionKind.SNAPPY,
                compression_strategy=pyorc.CompressionStrategy.COMPRESSION,
            ) as writer:
                for individual in array:
                    for term, label, typ in extract_terms([jsons.dump(individual)]):
                        row = ("individuals", individual.id, term, label, typ)
                        writer.write(row)


if __name__ == "__main__":
    pass
