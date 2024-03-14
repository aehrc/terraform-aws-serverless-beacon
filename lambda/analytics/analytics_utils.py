import csv
import json
from typing import List, Union

from pydantic import TypeAdapter
from shared.apiutils import (
    AlphanumericFilter,
    AuthError,
    CustomFilter,
    OntologyFilter,
    RequestQueryParams,
    VariantEffect,
)
from shared.utils import ENV_ATHENA
from smart_open import open as sopen


def parse_filters(
    filters: List[dict],
) -> List[Union[AlphanumericFilter, OntologyFilter, CustomFilter]]:
    adapter = TypeAdapter(List[Union[AlphanumericFilter, OntologyFilter, CustomFilter]])
    return adapter.validate_python(filters)


def parse_varinats(variants: List[dict]) -> List[RequestQueryParams]:
    adapter = TypeAdapter(List[RequestQueryParams])
    return adapter.validate_python(variants)


def parse_variant_effects(effects: Union[List[str], str]) -> List[VariantEffect]:
    if type(effects) != list:
        effects = effects.strip().replace(" ", "").split(",")
    adapter = TypeAdapter(List[VariantEffect])
    return adapter.validate_python(effects)


def load_svep(url):
    svep_data = dict()

    with sopen(url) as s3f:
        reader = csv.reader(s3f)
        for n, row in enumerate(reader):
            if n == 0:
                continue
            chr, ref, alt, pos, con = row
            svep_data[(chr, ref, alt, pos)] = parse_variant_effects(
                con.strip().split(",")
            )
    return svep_data


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


def datasets_query(assembly_id):
    query = f"""
    SELECT D.id, D._vcflocations, D._vcfchromosomemap, D.info, count(A._vcfsampleid) as numsamples, ARRAY_AGG(A._vcfsampleid) as samples
    FROM "{ENV_ATHENA.ATHENA_METADATA_DATABASE}"."{ENV_ATHENA.ATHENA_DATASETS_TABLE}" D
    JOIN "{ENV_ATHENA.ATHENA_METADATA_DATABASE}"."{ENV_ATHENA.ATHENA_ANALYSES_TABLE}" A
    ON A._datasetid = D.id
    GROUP by D.id, D._vcflocations, D._vcfchromosomemap, D._assemblyid, D.info
    HAVING D._assemblyid='{assembly_id}' 
    """
    return query


def filtered_datasets_with_samples_query(conditions, assembly_id):
    query = f"""
    SELECT D.id, D._vcflocations, D._vcfchromosomemap, D.info, ARRAY_AGG(A._vcfsampleid) as samples
    FROM "{ENV_ATHENA.ATHENA_METADATA_DATABASE}"."{ENV_ATHENA.ATHENA_ANALYSES_TABLE}" A
    JOIN "{ENV_ATHENA.ATHENA_METADATA_DATABASE}"."{ENV_ATHENA.ATHENA_DATASETS_TABLE}" D
    ON A._datasetid = D.id
    {conditions} 
    AND D._assemblyid='{assembly_id}' 
    GROUP BY D.id, D._vcflocations, D._vcfchromosomemap, D.info 
    """
    return query


def authenticate_analytics(event, context):
    authorizer = event["requestContext"]["authorizer"]
    groups = authorizer["claims"]["cognito:groups"].split(",")

    if not "record-access-user-group" in groups:
        raise AuthError(
            error_code="Unauthorised",
            error_message="User does not have access",
        )
