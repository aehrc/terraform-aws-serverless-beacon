from collections import defaultdict, OrderedDict
import json
import base64

import jsons

from shared.variantutils import perform_variant_search
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


def get_count_query(dataset_id, sample_names):
    query = f"""
    SELECT count("{{database}}"."{ENV_ATHENA.ATHENA_ANALYSES_TABLE}".id) as cnt
    FROM 
        "{{database}}"."{ENV_ATHENA.ATHENA_ANALYSES_TABLE}"
    WHERE
            "{{database}}"."{ENV_ATHENA.ATHENA_ANALYSES_TABLE}"._datasetid='{dataset_id}' 
        AND
            "{{database}}"."{ENV_ATHENA.ATHENA_ANALYSES_TABLE}"._vcfsampleid 
        IN 
            ({','.join([f"'{sn}'" for sn in sample_names])})
    """
    return query


def get_record_query(dataset_id, sample_names):
    query = f"""
    SELECT "{{database}}"."{ENV_ATHENA.ATHENA_INDIVIDUALS_TABLE}".* 
    FROM 
        "{{database}}"."{ENV_ATHENA.ATHENA_INDIVIDUALS_TABLE}" JOIN "{{database}}"."{ENV_ATHENA.ATHENA_ANALYSES_TABLE}"
    ON 
        "{{database}}"."{ENV_ATHENA.ATHENA_ANALYSES_TABLE}".individualid
        =
        "{{database}}"."{ENV_ATHENA.ATHENA_INDIVIDUALS_TABLE}".id
    WHERE 
            "{{database}}"."{ENV_ATHENA.ATHENA_INDIVIDUALS_TABLE}"._datasetid='{dataset_id}' 
        AND 
            "{{database}}"."{ENV_ATHENA.ATHENA_ANALYSES_TABLE}"._datasetid='{dataset_id}' 
        AND
            "{{database}}"."{ENV_ATHENA.ATHENA_ANALYSES_TABLE}"._vcfsampleid 
        IN 
            ({','.join([f"'{sn}'" for sn in sample_names])})
    """

    return query


def route(request: RequestParams, variant_id):
    dataset_hash = base64.b64decode(variant_id.encode()).decode()
    assembly_id, reference_name, pos, reference_bases, alternate_bases = dataset_hash.split(
        "\t"
    )
    pos = int(pos) - 1
    start = [pos]
    end = [pos + len(alternate_bases)]
    dataset_samples = defaultdict(set)

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

    query_responses = perform_variant_search(
        datasets=datasets,
        reference_name=reference_name,
        reference_bases=reference_bases,
        alternate_bases=alternate_bases,
        start=start,
        end=end,
        requested_granularity="record",  # we need the records for this task
        dataset_samples=samples,
        include_samples=True,
    )

    exists = False

    for query_response in query_responses:
        exists = exists or query_response.exists

        if query_response.exists:
            if request.query.requested_granularity == "boolean":
                break
            dataset_samples[query_response.dataset_id].update(
                sorted(query_response.sample_names)
            )

    queries = []

    dataset_samples_sorted = OrderedDict(sorted(dataset_samples.items()))
    iterated_individuals = 0
    chosen_individuals = 0
    total_individuals = sum([len(sample_names) for sample_names in dataset_samples_sorted.values()])

    for dataset_id, sample_names in dataset_samples_sorted.items():
        if len(sample_names) > 0 and request.query.requested_granularity == Granularity.RECORD:
            # TODO optimise for duplicate individuals
            chosen_samples = []

            for sample_name in sample_names:
                iterated_individuals += 1
                if (
                    iterated_individuals > request.query.pagination.skip
                    and chosen_individuals < request.query.pagination.limit
                ):
                    chosen_samples.append(sample_name)
                    chosen_individuals += 1

                if chosen_individuals == request.query.pagination.limit:
                    break
            if len(chosen_samples) > 0:
                query = get_record_query(dataset_id, chosen_samples)
                queries.append(query)

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
        query = " UNION ".join(queries)
        individuals = Individual.get_by_query(query) if len(queries) > 0 else []
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
