from collections import defaultdict
import json
import base64

from variantutils.search_variants import perform_variant_search_sync
from athena.common import run_custom_query
from athena.dataset import Dataset, parse_datasets_with_samples
from athena.filter_functions import entity_search_conditions
from apiutils.requests import RequestParams, Granularity
import apiutils.responses as responses
from apiutils.schemas import DefaultSchemas
import apiutils.entries as entries
from utils.lambda_utils import ENV_ATHENA


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


def route(request: RequestParams, variant_id):
    dataset_hash = base64.b64decode(variant_id.encode()).decode()
    assemblyId, referenceName, pos, referenceBases, alternateBases = dataset_hash.split(
        "\t"
    )
    pos = int(pos) - 1
    start = [pos]
    end = [pos + len(alternateBases)]

    conditions, execution_parameters = entity_search_conditions(
        request.query.filters, "analyses", "analyses", id_modifier="A.id"
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

    variants = set()
    results = list()
    found = set()
    # key=pos-ref-alt
    # val=counts
    variant_call_counts = defaultdict(int)
    variant_allele_counts = defaultdict(int)

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
        requestedGranularity=request.query.requested_granularity,
        includeResultsetResponses="ALL",
        dataset_samples=samples,
    )

    exists = False

    for query_response in query_responses:
        exists = exists or query_response.exists

        if exists:
            if request.query.requested_granularity == "boolean":
                break
            variants.update(query_response.variants)

            for variant in query_response.variants:
                chrom, pos, ref, alt, typ = variant.split("\t")
                idx = f"{pos}_{ref}_{alt}"
                variant_call_counts[idx] += query_response.call_count
                variant_allele_counts[idx] += query_response.all_alleles_count
                internal_id = f"{assemblyId}\t{chrom}\t{pos}\t{ref}\t{alt}"

                if internal_id not in found:
                    results.append(
                        entries.get_variant_entry(
                            base64.b64encode(f"{internal_id}".encode()).decode(),
                            assemblyId,
                            ref,
                            alt,
                            int(pos),
                            int(pos) + len(alt),
                            typ,
                        )
                    )
                    found.add(internal_id)

    if request.query.requested_granularity == Granularity.BOOLEAN:
        response = responses.build_beacon_boolean_response(
            {}, 1 if exists else 0, request, {}, DefaultSchemas.GENOMICVARIATIONS
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return responses.bundle_response(200, response)

    if request.query.requested_granularity == Granularity.COUNT:
        response = responses.build_beacon_count_response(
            {}, len(variants), request, {}, DefaultSchemas.GENOMICVARIATIONS
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return responses.bundle_response(200, response)

    if request.query.requested_granularity == Granularity.RECORD:
        response = responses.build_beacon_resultset_response(
            results, len(variants), request, {}, DefaultSchemas.GENOMICVARIATIONS
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return responses.bundle_response(200, response)
