import itertools
import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from typing import List

import numpy as np
import scipy.stats as stats
from analytics_utils import (
    authenticate_analytics,
    datasets_query,
    filtered_datasets_with_samples_query,
    load_svep,
    parse_athena_result,
    parse_filters,
    parse_variant_effects,
    parse_varinats,
)
from shared.apiutils import (
    Granularity,
    IncludeResultsetResponses,
    RequestQueryParams,
    VariantEffect,
)
from shared.apiutils.router import LambdaRouter
from shared.athena import Dataset, entity_search_conditions, run_custom_query
from shared.variantutils import perform_variant_search

router = LambdaRouter()
executor = ThreadPoolExecutor(32)


def tuples_to_list_str(tuples):
    return str(
        list([list(item) if isinstance(item, tuple) else item for item in tuples])
    )


def get_unique_subsets(count):
    all_subsets = []
    for r in range(2, count + 1):
        for subset in itertools.combinations(range(count), r):
            all_subsets.append(subset)
    return all_subsets


def get_datasets_by_filter(metadata_filter, assembly_id):
    filter_conditions, execution_parameters = entity_search_conditions(
        [metadata_filter], "analyses", "analyses", id_modifier="A.id"
    )
    filtered_datasets_arr = parse_athena_result(
        run_custom_query(
            filtered_datasets_with_samples_query(filter_conditions, assembly_id),
            return_id=True,
            execution_parameters=execution_parameters,
        )
    )

    return filtered_datasets_arr


def pre_process_datasets(all_datasets_arr):
    for dataset in all_datasets_arr:
        dataset["samples"] = (
            dataset["samples"].replace("[", "").replace("]", "").split(", ")
        )
        # load svep result if available, else put a placeholder
        if svep_data := dataset.get("info", dict()).get("svep_data"):
            dataset["info"]["svep_data"] = load_svep(svep_data)
        else:
            dataset["info"]["svep_data"] = dict()
    return all_datasets_arr


def get_datasets(metadata_filters, assembly_id):
    filtered_datasets = dict()
    # all datasets futures
    result_id_future = executor.submit(
        run_custom_query, datasets_query(assembly_id), return_id=True
    )
    # filtered results futures
    for filter_index, metadata_filter in enumerate(metadata_filters):
        filtered_datasets[filter_index] = executor.submit(
            get_datasets_by_filter, metadata_filter, assembly_id
        )
    # all datasets results
    all_datasets_arr = parse_athena_result(result_id_future.result())
    all_datasets_arr = pre_process_datasets(all_datasets_arr)
    # filtered results
    for filter_index, metadata_filter in enumerate(metadata_filters):
        filtered_datasets[filter_index] = filtered_datasets[filter_index].result()
        for dataset in filtered_datasets[filter_index]:
            dataset["samples"] = (
                dataset["samples"].replace("[", "").replace("]", "").split(", ")
            )
    return all_datasets_arr, filtered_datasets


def get_all_variant_hits(
    all_datasets_arr,
    variant_filters: List[RequestQueryParams],
    variant_effect_filters: List[VariantEffect],
):
    all_variant_hits = {dataset["id"]: dict() for dataset in all_datasets_arr}
    dataset_svep = {
        dataset["id"]: dataset["info"]["svep_data"] for dataset in all_datasets_arr
    }
    responses = []

    for n, params in enumerate(variant_filters):
        responses.append(
            executor.submit(
                perform_variant_search,
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
        )

    for n, params in enumerate(variant_filters):
        query_responses = responses[n].result()
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
                variant_effects = dataset_svep[dataset_id].get(
                    (chrom, ref, alt, pos), []
                )
                valid_variant = len(variant_effect_filters) == 0 or any(
                    [effect in variant_effects for effect in variant_effect_filters]
                )

                if valid_variant:
                    entry["variants"].append(
                        {
                            "chrom": chrom,
                            "pos": pos,
                            "ref_base": ref,
                            "alt_base": alt,
                            "effects": tuple(variant_effects),
                        }
                    )
    return all_variant_hits


@router.attach("/analytics/v_correlations", "post", authenticate_analytics)
def variant_correlations(event, context):
    """
    Compute correlation between the variants mentioned and the phenotypes
    provided as metadata filters
    """
    body_dict = json.loads(event.get("body"))
    metadata_filters = parse_filters(body_dict.get("filters", []))
    variant_filters = parse_varinats(body_dict.get("variants", []))
    variant_effect_filters = parse_variant_effects(body_dict.get("variant_effects", []))
    assembly_id = variant_filters[0].assembly_id

    # get all with svep result and filtered datasets
    all_datasets_arr, filtered_datasets = get_datasets(metadata_filters, assembly_id)
    # get all variants
    all_variant_hits = get_all_variant_hits(
        all_datasets_arr, variant_filters, variant_effect_filters
    )

    # dataset IDs transforming into array indexes
    dataset_index = {
        dataset["id"]: index for index, dataset in enumerate(all_datasets_arr)
    }
    # following dictionaries are keyed by the position index from queries
    # values are obtained per dataset; can be either numeric (frequency)
    # or arrays (samples observed in each dataset)
    #
    # grouped by filter index
    filter_frequencies = defaultdict(lambda: [0 for _ in all_datasets_arr])
    query_filter_samples = defaultdict(lambda: [[] for _ in all_datasets_arr])
    # grouped by variant(queried) index
    variant_frequencies = defaultdict(lambda: [0 for _ in all_datasets_arr])
    query_variant_samples = defaultdict(lambda: [[] for _ in all_datasets_arr])
    query_variant_hits = defaultdict(lambda: [[] for _ in all_datasets_arr])

    # filter frequencies
    for index, datasets in filtered_datasets.items():
        for dataset in datasets:
            dix = dataset_index[dataset["id"]]
            filter_frequencies[index][dix] = len(dataset["samples"])
            query_filter_samples[index][dix] = dataset["samples"]

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
            query_variant_samples[indexes][dix] = list(samples_intersection)
            query_variant_hits[indexes][dix] = [
                dict(zip(["chrom", "pos", "ref_base", "alt_base", "effects"], hit))
                for hit in variants_hit
            ]

    filter_variant_correlations = dict()
    filter_variant_intersections = dict()

    # variables must be paired to compute pearson r
    # so we check filter freq againt variant freq, subjected to the presence of filter
    # Pearsons Assumption -
    # Pearson's correlation coefficient assumes a linear relationship between the two variables.
    # If the occurrences of the two variables are independent of each other or
    # if their relationship is not linear, Pearson's r might not be the best measure of their association.
    for f_index, f_samples in query_filter_samples.items():
        for v_index, v_samples in query_variant_samples.items():
            f_freqs = [len(f_sample) for f_sample in f_samples]
            v_freqs = [
                len(set(f_sample).intersection(v_samples[d_index]))
                for d_index, f_sample in enumerate(f_samples)
            ]
            statistic, p_value = stats.pearsonr(f_freqs, v_freqs)

            if np.isnan(statistic) or np.isnan(p_value):
                statistic, p_value = "NaN", "Nan"

            filter_variant_correlations[(f_index, v_index)] = (statistic, p_value)
            filter_variant_intersections[(f_index, v_index)] = [
                list(set(f_sample).intersection(v_samples[d_index]))
                for d_index, f_sample in enumerate(f_samples)
            ]

    result = {
        "dataset_ids": [dataset["id"] for dataset in all_datasets_arr],
        "filter_frequencies": {str(k): v for k, v in filter_frequencies.items()},
        "query_filter_samples": {str(k): v for k, v in query_filter_samples.items()},
        "variant_frequencies": {
            tuples_to_list_str(k): v for k, v in variant_frequencies.items()
        },
        # convert tuples to str format lists so that javascript can parse them
        "query_variant_samples": {
            tuples_to_list_str(k): v for k, v in query_variant_samples.items()
        },
        "query_variant_hits": {
            tuples_to_list_str(k): v for k, v in query_variant_hits.items()
        },
        "filter_variant_correlations": {
            tuples_to_list_str(k): v for k, v in filter_variant_correlations.items()
        },
        "filter_variant_intersections": {
            tuples_to_list_str(k): v for k, v in filter_variant_intersections.items()
        },
    }

    return {"result": result, "success": True}


if __name__ == "__main__":
    event = {"body": open("test.json").read()}
    res = variant_correlations(event, {})

    print(json.dumps(res))
    pass
