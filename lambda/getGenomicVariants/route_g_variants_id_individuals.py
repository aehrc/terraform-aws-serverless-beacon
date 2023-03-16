import os
from collections import defaultdict, OrderedDict
import json
import base64

import jsons

from variantutils.search_variants import perform_variant_search_sync
from athena.dataset import Dataset, parse_datasets_with_samples
from athena.common import run_custom_query
from athena.filter_functions import entity_search_conditions
from athena.individual import Individual
from apiutils.requests import RequestParams, Granularity
import apiutils.responses as responses
from apiutils.schemas import DefaultSchemas


ATHENA_DATASETS_TABLE = os.environ["ATHENA_DATASETS_TABLE"]
ATHENA_INDIVIDUALS_TABLE = os.environ["ATHENA_INDIVIDUALS_TABLE"]
ATHENA_ANALYSES_TABLE = os.environ["ATHENA_ANALYSES_TABLE"]
ATHENA_METADATA_DATABASE = os.environ["ATHENA_METADATA_DATABASE"]


def datasets_query(conditions, assembly_id):
    query = f"""
    SELECT D.id, D._vcflocations, D._vcfchromosomemap, ARRAY_AGG(A._vcfsampleid) as samples
    FROM "{ATHENA_METADATA_DATABASE}"."{ATHENA_ANALYSES_TABLE}" A
    JOIN "{ATHENA_METADATA_DATABASE}"."{ATHENA_DATASETS_TABLE}" D
    ON A._datasetid = D.id
    {conditions} 
    AND D._assemblyid='{assembly_id}' 
    GROUP BY D.id, D._vcflocations, D._vcfchromosomemap 
    """
    return query


def datasets_query_fast(assembly_id):
    query = f"""
    SELECT id, _vcflocations, _vcfchromosomemap
    FROM "{ATHENA_METADATA_DATABASE}"."{ATHENA_DATASETS_TABLE}"
    WHERE _assemblyid='{assembly_id}' 
    """
    return query


def get_count_query(dataset_id, sample_names):
    query = f"""
    SELECT count("{{database}}"."{ATHENA_ANALYSES_TABLE}".id) as cnt
    FROM 
        "{{database}}"."{ATHENA_ANALYSES_TABLE}"
    WHERE
            "{{database}}"."{ATHENA_ANALYSES_TABLE}"._datasetid='{dataset_id}' 
        AND
            "{{database}}"."{ATHENA_ANALYSES_TABLE}"._vcfsampleid 
        IN 
            ({','.join([f"'{sn}'" for sn in sample_names])})
    """
    return query


def get_record_query(dataset_id, sample_names):
    query = f"""
    SELECT "{{database}}"."{ATHENA_INDIVIDUALS_TABLE}".* 
    FROM 
        "{{database}}"."{ATHENA_INDIVIDUALS_TABLE}" JOIN "{{database}}"."{ATHENA_ANALYSES_TABLE}"
    ON 
        "{{database}}"."{ATHENA_ANALYSES_TABLE}".individualid
        =
        "{{database}}"."{ATHENA_INDIVIDUALS_TABLE}".id
    WHERE 
            "{{database}}"."{ATHENA_INDIVIDUALS_TABLE}"._datasetid='{dataset_id}' 
        AND 
            "{{database}}"."{ATHENA_ANALYSES_TABLE}"._datasetid='{dataset_id}' 
        AND
            "{{database}}"."{ATHENA_ANALYSES_TABLE}"._vcfsampleid 
        IN 
            ({','.join([f"'{sn}'" for sn in sample_names])})
    """

    return query


def route(request: RequestParams, variant_id):
    dataset_hash = base64.b64decode(variant_id.encode()).decode()
    assemblyId, referenceName, pos, referenceBases, alternateBases = dataset_hash.split(
        "\t"
    )
    pos = int(pos) - 1
    start = [pos]
    end = [pos + len(alternateBases)]
    dataset_samples = defaultdict(set)

    conditions, execution_parameters = entity_search_conditions(
        request.query.filters, "analyses", "individuals", id_modifier="A.id"
    )

    if conditions:
        query = datasets_query(conditions, assemblyId)
        exec_id = run_custom_query(
            query, return_id=True, execution_parameters=execution_parameters
        )
        datasets, samples = parse_datasets_with_samples(exec_id)
    else:
        query = datasets_query_fast(assemblyId)
        datasets = Dataset.get_by_query(
            query, execution_parameters=execution_parameters
        )
        samples = []

    query_responses = perform_variant_search_sync(
        datasets=datasets,
        referenceName=referenceName,
        referenceBases=referenceBases,
        alternateBases=alternateBases,
        start=start,
        end=end,
        variantType=None,
        variantMinLength=0,
        variantMaxLength=-1,
        requestedGranularity="record",  # we need the records for this task
        includeResultsetResponses="ALL",
        dataset_samples=samples,
        passthrough={"includeSamples": True},
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

    for dataset_id, sample_names in dataset_samples_sorted.items():
        if (len(sample_names)) > 0:
            if request.query.requested_granularity == "count":
                # query = get_count_query(dataset_id, sample_names)
                # queries.append(query)
                # TODO optimise for duplicate individuals
                iterated_individuals += len(sample_names)
            elif request.query.requested_granularity == Granularity.RECORD:
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

    if request.query.requested_granularity == "boolean":
        response = responses.build_beacon_boolean_response(
            {}, 1 if exists else 0, request, {}, DefaultSchemas.INDIVIDUALS
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return responses.bundle_response(200, response)

    if request.query.requested_granularity == "count":
        count = iterated_individuals
        response = responses.build_beacon_count_response(
            {}, count, request, {}, DefaultSchemas.INDIVIDUALS
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return responses.bundle_response(200, response)

    if request.query.requested_granularity == Granularity.RECORD:
        query = " UNION ".join(queries)
        individuals = Individual.get_by_query(query) if len(queries) > 0 else []
        response = responses.build_beacon_resultset_response(
            jsons.dump(individuals, strip_privates=True),
            len(individuals),
            request,
            {},
            DefaultSchemas.INDIVIDUALS,
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return responses.bundle_response(200, response)


if __name__ == "__main__":
    pass
