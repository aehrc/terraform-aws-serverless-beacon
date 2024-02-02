import json
import threading
from copy import deepcopy
from typing import List
from collections import defaultdict
import itertools

import scipy.stats as stats
import numpy as np

from util import (
    parse_filters,
    parse_athena_result,
    parse_varinats,
    datasets_query,
    filtered_datasets_with_samples_query,
)
from shared.athena import entity_search_conditions
from shared.apiutils.router import path_pattern_matcher, BeaconError
from shared.variantutils import perform_variant_search
from shared.utils import ENV_ATHENA
from shared.athena import (
    Dataset,
    run_custom_query,
    entity_search_conditions,
)
from shared.apiutils import Granularity, IncludeResultsetResponses, RequestQueryParams


def get_unique_subsets(count):
    all_subsets = []
    for r in range(2, count + 1):
        for subset in itertools.combinations(range(count), r):
            all_subsets.append(subset)
    return all_subsets


def get_datasets_by_filter(metadata_filter):
    filter_conditions, execution_parameters = entity_search_conditions(
        [metadata_filter], "analyses", "analyses", id_modifier="A.id"
    )
    filtered_datasets_arr = parse_athena_result(
        run_custom_query(
            filtered_datasets_with_samples_query(filter_conditions, "GRCH38"),
            return_id=True,
            execution_parameters=execution_parameters,
        )
    )

    return filtered_datasets_arr


def get_all_datasets():
    all_datasets_arr = parse_athena_result(
        run_custom_query(datasets_query("GRCH38"), return_id=True)
    )
    for dataset in all_datasets_arr:
        dataset["samples"] = (
            dataset["samples"].replace("[", "").replace("]", "").split(", ")
        )
    return all_datasets_arr


def get_filtered_datasets(metadata_filters):
    filtered_datasets = dict()
    for filter_index, metadata_filter in enumerate(metadata_filters):
        filtered_datasets[filter_index] = get_datasets_by_filter(metadata_filter)
        for dataset in filtered_datasets[filter_index]:
            dataset["samples"] = (
                dataset["samples"].replace("[", "").replace("]", "").split(", ")
            )
    return filtered_datasets


def get_all_variant_hits(all_datasets_arr, variant_filters: List[RequestQueryParams]):
    all_variant_hits = {dataset["id"]: dict() for dataset in all_datasets_arr}
    for n, params in enumerate(variant_filters):
        query_responses = perform_variant_search(
            datasets=[
                Dataset(
                    id=dataset["id"],
                    vcfChromosomeMap=dataset["_vcfchromosomemap"],
                    vcfLocations=dataset["_vcflocations"],
                )
                for dataset in all_datasets_arr
            ],
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

            if n not in all_variant_hits[dataset_id]:
                all_variant_hits[dataset_id][n] = deepcopy(aggregate_response)

            entry = all_variant_hits[dataset_id][n]
            entry["variant_samples"] += response.sample_names

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
    return all_variant_hits


@path_pattern_matcher("v_correlations", "post")
def variant_correlations(event):
    """
    Compute correlation between the variants mentioned and the phenotypes
    provided as metadata filters
    """
    body_dict = json.loads(event.get("body"))
    metadata_filters = parse_filters(body_dict.get("filters", []))
    variant_filters = parse_varinats(body_dict.get("variants", []))

    # get all datasets
    all_datasets_arr = get_all_datasets()
    # # get filtered datasets and samples to scan
    filtered_datasets = get_filtered_datasets(metadata_filters)

    # get all variants
    all_variant_hits = get_all_variant_hits(all_datasets_arr, variant_filters)

    # building the dataset for correlation computation
    # for each filter we need a table like below
    # Dataset    |      1     |      2      |      3      |      4      |
    # -------------------------------------------------------------------
    # Disease    |  x:5 y:10  |  x:10 y:20  |  x:15 y:30  |  x:20 y:40  |
    # Variant    |  p:5 q:10  |  p:10 q:20  |  p:15 q:30  |  p:20 q:40  |

    # dataset IDs transforming into array indexes
    dataset_index = {
        dataset["id"]: index for index, dataset in enumerate(all_datasets_arr)
    }
    # grouped by filter index
    filter_frequencies = defaultdict(lambda: [0 for _ in all_datasets_arr])
    # grouped by variant(queried) index
    variant_frequencies = defaultdict(lambda: [0 for _ in all_datasets_arr])
    query_variant_samples = defaultdict(lambda: [0 for _ in all_datasets_arr])
    query_variant_hits = defaultdict(lambda: [0 for _ in all_datasets_arr])

    # filter frequencies
    for index, datasets in filtered_datasets.items():
        for dataset in datasets:
            dix = dataset_index[dataset["id"]]
            filter_frequencies[index][dix] = len(dataset["samples"])

    # variant frequencies
    for dataset_id, variants_results in all_variant_hits.items():
        dix = dataset_index[dataset_id]
        for index, variants_result in variants_results.items():
            variant_frequencies[(index,)][dix] = len(variants_result["variant_samples"])
            query_variant_samples[(index,)][dix] = variants_result["variant_samples"]
            query_variant_hits[(index,)][dix] = variants_result["variants"]

        # combined frequencies AND operator between queries variants
        for indexes in get_unique_subsets(len(variants_results)):
            samples_intersection = set(variants_results[indexes[0]]["variant_samples"])
            variants_hit = set(
                tuple(
                    [
                        tuple(v.values())
                        for v in variants_results[indexes[0]]["variants"]
                    ]
                )
            )

            for next_index in indexes[1:]:
                samples_intersection = samples_intersection.intersection(
                    variants_results[next_index]["variant_samples"]
                )
                variants_hit.update(
                    tuple(
                        [
                            tuple(v.values())
                            for v in variants_results[next_index]["variants"]
                        ]
                    )
                )
            variant_frequencies[indexes][dix] = len(samples_intersection)
            query_variant_samples[indexes][dix] = len(samples_intersection)
            query_variant_hits[indexes][dix] = [
                dict(zip(["chrom", "pos", "ref_base", "alt_base"], hit))
                for hit in variants_hit
            ]

    correlations = dict()

    for f_index, f_freqs in filter_frequencies.items():
        for v_index, v_freqs in variant_frequencies.items():
            statistic, p_value = stats.pearsonr(f_freqs, v_freqs)
            correlations[(f_index, v_index)] = (statistic, p_value)

    result = {
        "dataset_ids": [dataset["id"] for dataset in all_datasets_arr],
        "filter_frequencies": {str(k): v for k, v in filter_frequencies.items()},
        "variant_frequencies": {str(k): v for k, v in variant_frequencies.items()},
        "query_variant_samples": {str(k): v for k, v in query_variant_samples.items()},
        "query_variant_hits": {str(k): v for k, v in query_variant_hits.items()},
        "correlations": {str(k): v for k, v in correlations.items()},
        "v_queries_results": [dataset["id"] for dataset in all_datasets_arr],
    }

    return {"result": result, "success": True}


if __name__ == "__main__":
    pass
