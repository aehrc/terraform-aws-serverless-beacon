import json
import csv
import sys

import jsons
import boto3
import pyorc
from smart_open import open as sopen

from .common import AthenaModel, extract_terms
from shared.utils import ENV_ATHENA


s3 = boto3.client("s3")
athena = boto3.client("athena")
csv.field_size_limit(sys.maxsize)


class Dataset(jsons.JsonSerializable, AthenaModel):
    _table_name = ENV_ATHENA.ATHENA_DATASETS_TABLE
    # for saving to database order matter
    _table_columns = [
        "id",
        "_assemblyId",
        "_vcfLocations",
        "_vcfChromosomeMap",
        "createDateTime",
        "dataUseConditions",
        "description",
        "externalUrl",
        "info",
        "name",
        "updateDateTime",
        "version",
    ]

    def __init__(
        self,
        *,
        id="",
        assemblyId="",
        vcfLocations="",
        vcfChromosomeMap="",
        createDateTime="",
        dataUseConditions={},
        description="",
        externalUrl="",
        info={},
        name="",
        updateDateTime="",
        version="",
    ):
        self.id = id
        self._assemblyId = assemblyId
        self._vcfLocations = vcfLocations
        self._vcfChromosomeMap = vcfChromosomeMap
        self.createDateTime = createDateTime
        self.dataUseConditions = dataUseConditions
        self.description = description
        self.externalUrl = externalUrl
        self.info = info
        self.name = name
        self.updateDateTime = updateDateTime
        self.version = version

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
        key = f"{array[0].id}-datasets"

        with sopen(f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/datasets/{key}", "wb") as s3file:
            with pyorc.Writer(
                s3file,
                header,
                compression=pyorc.CompressionKind.SNAPPY,
                compression_strategy=pyorc.CompressionStrategy.COMPRESSION,
                bloom_filter_columns=bloom_filter_columns,
            ) as writer:
                for dataset in array:
                    row = tuple(
                        dataset.__dict__[k]
                        if type(dataset.__dict__[k]) == str
                        else json.dumps(dataset.__dict__[k])
                        for k in cls._table_columns
                    )
                    writer.write(row)

        header = "struct<kind:string,id:string,term:string,label:string,type:string>"
        with sopen(
            f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/terms-cache/datasets-{key}", "wb"
        ) as s3file:
            with pyorc.Writer(
                s3file,
                header,
                compression=pyorc.CompressionKind.SNAPPY,
                compression_strategy=pyorc.CompressionStrategy.COMPRESSION,
            ) as writer:
                for dataset in array:
                    for term, label, typ in extract_terms([jsons.dump(dataset)]):
                        row = ("datasets", dataset.id, term, label, typ)
                        writer.write(row)


def get_datasets(
    assembly_id, dataset_id=None, dataset_ids=None, conditions="", skip=0, limit=100
):
    if dataset_id:
        query = f"""
            SELECT id, _vcflocations, _vcfchromosomemap 
            FROM "{{database}}"."{{table}}" 
            WHERE _assemblyid='{assembly_id}' 
            AND id='{dataset_id}'
            LIMIT 1
        """
    elif dataset_ids:
        query = f"""
            SELECT id, _vcflocations, _vcfchromosomemap 
            FROM "{{database}}"."{{table}}" 
            WHERE _assemblyid='{assembly_id}' 
            AND id IN ({','.join([f"'{id}'" for id in dataset_ids])})
            ORDER BY id 
            OFFSET {skip} 
            LIMIT {limit};
        """
    else:
        query = f"""
            SELECT id, _vcflocations, _vcfchromosomemap 
            FROM "{{database}}"."{{table}}" 
            WHERE _assemblyid='{assembly_id}' 
            ORDER BY id 
            OFFSET {skip} 
            LIMIT {limit};
        """
    return Dataset.get_by_query(query)


def parse_datasets_with_samples(exec_id):
    datasets = []
    samples = []

    var_list = list()
    case_map = {k.lower(): k for k in Dataset().__dict__.keys()}

    with sopen(f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/query-results/{exec_id}.csv") as s3f:
        reader = csv.reader(s3f)

        for n, row in enumerate(reader):
            if n == 0:
                var_list = row
            else:
                instance = Dataset()
                for attr, val in zip(var_list, row):
                    if attr == "samples":
                        samples.append(
                            val.replace("[", "").replace("]", "").split(", ")
                        )
                    elif attr not in case_map:
                        continue
                    else:
                        try:
                            val = json.loads(val)
                        except:
                            val = val
                        instance.__dict__[case_map[attr]] = val
                datasets.append(instance)

    return datasets, samples


if __name__ == "__main__":
    pass
