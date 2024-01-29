import csv
import json

from smart_open import open as sopen

from typing import List, Optional, Tuple, Union, Annotated
from pydantic import (
    ConfigDict,
    BaseModel,
    TypeAdapter,
    ValidationError,
    ValidationInfo,
    PrivateAttr,
    constr,
    field_validator,
    model_validator,
)

from shared.apiutils import (
    AlphanumericFilter,
    OntologyFilter,
    CustomFilter,
    RequestQueryParams,
)
from shared.utils import ENV_ATHENA


def parse_filters(
    filters: List[dict],
) -> List[Union[AlphanumericFilter, OntologyFilter, CustomFilter]]:
    adapter = TypeAdapter(List[Union[AlphanumericFilter, OntologyFilter, CustomFilter]])
    return adapter.validate_python(filters)


def parse_varinats(variants: List[dict]) -> List[RequestQueryParams]:
    adapter = TypeAdapter(List[RequestQueryParams])
    return adapter.validate_python(variants)


def parse_athena_result(exec_id: str):
    entries = []
    with sopen(
        f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/query-results/{exec_id}.csv"
    ) as s3f:
        reader = csv.reader(s3f)

        for n, row in enumerate(reader):
            if n == 0:
                attributes = row
            else:
                instance = dict()
                for attr, val in zip(attributes, row):
                    try:
                        val = json.loads(val)
                    except:
                        val = val
                    instance[attr] = val
                entries.append(instance)

    return entries
