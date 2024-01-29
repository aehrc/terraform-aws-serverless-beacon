import json
import threading
from copy import deepcopy

from util import parse_filters, parse_athena_result, parse_varinats
from shared.athena import entity_search_conditions
from shared.apiutils.router import path_pattern_matcher, BeaconError
from shared.variantutils import perform_variant_search
from shared.utils import ENV_ATHENA
from shared.athena import (
    Dataset,
    run_custom_query,
    entity_search_conditions,
)
from shared.apiutils import Granularity, IncludeResultsetResponses

# TODO add multi-threading for queries

def datasets_query(assembly_id):
    query = f"""
    SELECT D.id, D._vcflocations, D._vcfchromosomemap, count(A._vcfsampleid) as numsamples, ARRAY_AGG(A._vcfsampleid) as samples
    FROM "{ENV_ATHENA.ATHENA_METADATA_DATABASE}"."{ENV_ATHENA.ATHENA_DATASETS_TABLE}" D
    JOIN "{ENV_ATHENA.ATHENA_METADATA_DATABASE}"."{ENV_ATHENA.ATHENA_ANALYSES_TABLE}" A
    ON A._datasetid = D.id
    GROUP by (D.id, D._vcflocations, D._vcfchromosomemap, D._assemblyid)
    HAVING D._assemblyid='{assembly_id}' 
    """
    return query


def filtered_datasets_with_samples_query(conditions, assembly_id):
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


@path_pattern_matcher("v_frequencies", "post")
def variant_frequencies(event):
    """
    Compute frequency of given variants subjecting to filters (if any) provided
    Results are grouped into datasets
    We also report the total number of analyses, analysis with filters
    and with variants asked for
    """
    body_dict = json.loads(event.get("body"))
    metadata_filters = parse_filters(body_dict.get("filters", []))
    variant_filters = parse_varinats(body_dict.get("variants", []))
    filter_conditions, execution_parameters = entity_search_conditions(
        metadata_filters, "analyses", "analyses", id_modifier="A.id"
    )
    result = dict()
    # get all datasets
    all_datasets_arr = parse_athena_result(
        run_custom_query(datasets_query("GRCH38"), return_id=True)
    )
    # get filtered datasets and samples to scan
    filtered_datasets_arr = parse_athena_result(
        run_custom_query(
            filtered_datasets_with_samples_query(filter_conditions, "GRCH38"),
            return_id=True,
            execution_parameters=execution_parameters,
        )
    )

    datasets = [
        Dataset(
            id=dataset["id"],
            vcfChromosomeMap=dataset["_vcfchromosomemap"],
            vcfLocations=dataset["_vcflocations"],
        )
        for dataset in filtered_datasets_arr
    ]
    dataset_samples = [
        dataset["samples"].replace("[", "").replace("]", "").split(", ")
        for dataset in filtered_datasets_arr
    ]

    for dataset in all_datasets_arr:
        result[dataset["id"]] = {
            "dataset_id": dataset["id"],
            "sample_count": dataset["numsamples"],
            "samples": dataset["samples"].replace("[", "").replace("]", "").split(", "),
            "v_queries": dict(),
        }

    for dataset in filtered_datasets_arr:
        arr = dataset["samples"].replace("[", "").replace("]", "").split(", ")
        result[dataset["id"]]["filtered_sample_count"] = len(arr)
        result[dataset["id"]]["filtered_samples"] = arr

    # perform variants search
    for n, params in enumerate(variant_filters):
        query_responses = perform_variant_search(
            datasets=datasets,
            reference_name=params.reference_name,
            reference_bases=params.reference_bases,
            alternate_bases=params.alternate_bases,
            start=params.start,
            end=params.end,
            variant_type=params.variant_type,
            variant_min_length=params.variant_min_length,
            variant_max_length=params.variant_max_length,
            requested_granularity=Granularity.RECORD,
            include_datasets=IncludeResultsetResponses.ALL,
            dataset_samples=dataset_samples,
            include_samples=True,
        )

        aggregate_response = {
            "variants": [],
            "variant_samples": [],
            "variant_sample_count": 0,
            "variant_call_count": 0,
        }

        # responses are retrieved per queried variant per VCF file (i.e., dataset)
        for response in query_responses:
            dataset_id = response.dataset_id

            if n not in result[dataset_id]["v_queries"]:
                result[dataset_id]["v_queries"][n] = deepcopy(aggregate_response)

            entry = result[dataset_id]["v_queries"][n]
            entry["variant_samples"] += response.sample_names
            entry["variant_sample_count"] += len(response.sample_names)
            entry["variant_call_count"] += response.call_count

            for variant in response.variants:
                (
                    chrom,
                    pos,
                    ref,
                    alt,
                    typ,
                ) = variant.strip().split("\t")
                entry["variants"].append(
                    {"chrom": chrom, "pos": pos, "ref_base": ref, "alt_base": alt}
                )

    # getting rid of named indices
    flattened_result = list(result.values())
    for result in flattened_result:
        result["v_queries"] = list(result["v_queries"].values())

    return {"result": flattened_result, "success": True}


if __name__ == "__main__":
    pass
