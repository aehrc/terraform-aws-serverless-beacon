from collections import defaultdict, OrderedDict
import json
import base64

import jsons

from shared.apiutils.s3tables import perform_sample_search_s3tables
from shared.utils import ENV_ATHENA
from shared.athena import (
    Individual,
    Dataset,
    parse_datasets_with_samples,
    entity_search_conditions,
    run_custom_query,
)
from shared.apiutils import (
    RequestParams,
    Granularity,
    DefaultSchemas,
    build_beacon_boolean_response,
    build_beacon_resultset_response,
    build_beacon_count_response,
    bundle_response,
)
from shared.apiutils.requests import RequestMeta, RequestQuery, RequestQueryParams


def datasets_query(conditions, assembly_id):
    query = f"""
    SELECT D.id, D._vcflocations, D._vcfchromosomemap, ARRAY_AGG(A._vcfsampleid) as samples
    FROM "{ENV_ATHENA.ATHENA_METADATA_DATABASE}"."{ENV_ATHENA.ATHENA_ANALYSES_TABLE}" A
    JOIN "{ENV_ATHENA.ATHENA_METADATA_DATABASE}"."{ENV_ATHENA.ATHENA_DATASETS_TABLE}" D
    ON A._datasetid = D.id
    {conditions} 
    AND D._assemblyid='{assembly_id}' 
    GROUP BY D.id, D._vcflocations, D._vcfchromosomemap 
    """
    return query


def datasets_query_fast(assembly_id):
    query = f"""
    SELECT id, _vcflocations, _vcfchromosomemap
    FROM "{ENV_ATHENA.ATHENA_METADATA_DATABASE}"."{ENV_ATHENA.ATHENA_DATASETS_TABLE}"
    WHERE _assemblyid='{assembly_id}' 
    """
    return query


def get_count_query(sample_names):
    query = f"""
    SELECT count("{{database}}"."{ENV_ATHENA.ATHENA_ANALYSES_TABLE}".id) as cnt
    FROM 
        "{{database}}"."{ENV_ATHENA.ATHENA_ANALYSES_TABLE}"
    WHERE
        "{{database}}"."{ENV_ATHENA.ATHENA_ANALYSES_TABLE}"._vcfsampleid 
        IN 
            ({','.join([f"'{sn}'" for sn in sample_names])})
    """
    return query


def get_record_query(sample_names):
    query = f"""
    SELECT "{{database}}"."{ENV_ATHENA.ATHENA_INDIVIDUALS_TABLE}".* 
    FROM 
        "{{database}}"."{ENV_ATHENA.ATHENA_INDIVIDUALS_TABLE}" JOIN "{{database}}"."{ENV_ATHENA.ATHENA_ANALYSES_TABLE}"
    ON 
        "{{database}}"."{ENV_ATHENA.ATHENA_ANALYSES_TABLE}".individualid
        =
        "{{database}}"."{ENV_ATHENA.ATHENA_INDIVIDUALS_TABLE}".id
    WHERE 
        "{{database}}"."{ENV_ATHENA.ATHENA_ANALYSES_TABLE}"._vcfsampleid 
        IN 
            ({','.join([f"'{sn}'" for sn in sample_names])})
    """

    return query


def route(request: RequestParams, variant_id):
    dataset_hash = base64.b64decode(variant_id.encode()).decode()
    assembly_id, reference_name, pos, reference_bases, alternate_bases = (
        dataset_hash.split("\t")
    )
    pos = int(pos)
    conditions, execution_parameters = entity_search_conditions(
        request.query.filters, "analyses", "individuals", id_modifier="A.id"
    )

    if conditions:
        query = datasets_query(conditions, assembly_id)
        exec_id = run_custom_query(
            query, return_id=True, execution_parameters=execution_parameters
        )
        datasets, samples = parse_datasets_with_samples(exec_id)
    else:
        query = datasets_query_fast(assembly_id)
        datasets = Dataset.get_by_query(
            query, execution_parameters=execution_parameters
        )
        samples = []

    samples = [item for sublist in samples for item in sublist]
    query_responses = perform_sample_search_s3tables(
        reference_name=reference_name,
        reference_bases=reference_bases,
        alternate_bases=alternate_bases,
        pos=pos,
        samples=samples,
    )
    samples = [entry["sample_name"] for entry in query_responses]
    exists = len(samples) > 0
    total_individuals = len(samples)

    query = get_record_query(samples)

    if request.query.requested_granularity == Granularity.BOOLEAN:
        response = build_beacon_boolean_response(
            {}, 1 if exists else 0, request, {}, DefaultSchemas.INDIVIDUALS
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == Granularity.COUNT:
        response = build_beacon_count_response(
            {}, total_individuals, request, {}, DefaultSchemas.INDIVIDUALS
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == Granularity.RECORD:
        individuals = Individual.get_by_query(query) if len(samples) > 0 else []
        response = build_beacon_resultset_response(
            jsons.dump(individuals, strip_privates=True),
            total_individuals,
            request,
            {},
            DefaultSchemas.INDIVIDUALS,
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return bundle_response(200, response)


if __name__ == "__main__":
    pass
