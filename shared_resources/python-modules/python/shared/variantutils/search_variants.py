from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import time
import copy

import jsons
import boto3

from .local_utils import split_query
from shared.utils import get_matching_chromosome
from shared.dynamodb import VariantQuery, VariantResponse
from shared.payloads import SplitQueryPayload, PerformQueryResponse


REQUEST_TIMEOUT = 600  # seconds
THREADS = 500


s3 = boto3.client("s3")


def perform_variant_search(
    *,
    datasets,
    reference_name,
    reference_bases,
    alternate_bases,
    start,
    end,
    variant_type=None,
    variant_min_length=0,
    variant_max_length=-1,
    requested_granularity="boolean",
    include_datasets="ALL",
    query_id="TEST",
    dataset_samples=[],
    include_samples=False,
):
    try:
        # get vcf file and the name of chromosome in it eg: "chr1", "Chr4", "CHR1" or just "1"
        vcf_chromosomes = {
            vcfm["vcf"]: get_matching_chromosome(vcfm["chromosomes"], reference_name)
            for dataset in datasets
            for vcfm in dataset._vcfChromosomeMap
        }

        if len(start) == 2:
            start_min, start_max = start
        else:
            start_min = start[0]

        if len(end) == 2:
            end_min, end_max = end
        else:
            end_min = start_min
            end_max = end[0]

        if len(start) != 2:
            start_max = end_max
    except Exception as e:
        print("Error occured ", e)
        return False, []

    start_min += 1
    start_max += 1
    end_min += 1
    end_max += 1

    print("Start: event publishing")
    executor = ThreadPoolExecutor(THREADS)
    futures = []

    # parallelism across datasets
    for n, dataset in enumerate(datasets):
        vcf_locations = {
            vcf: vcf_chromosomes[vcf]
            for vcf in dataset._vcfLocations
            if vcf_chromosomes[vcf]
        }

        # call split query for each dataset found
        payload = {
            "query_id": query_id,
            "dataset_id": dataset.id,
            "vcf_locations": vcf_locations,
            "samples": dataset_samples[n] if dataset_samples else [],
            "reference_bases": reference_bases or "N",
            "alternate_bases": alternate_bases or "N",
            "start_min": start_min,
            "start_max": start_max,
            "end_min": end_min,
            "end_max": end_max,
            "variant_min_length": variant_min_length,
            "variant_max_length": variant_max_length,
            "variant_type": variant_type,
            "include_datasets": include_datasets,
            "include_samples": include_samples,
            "requested_granularity": requested_granularity,
        }

        futures.append(executor.submit(split_query, payload))

    for future in as_completed(futures):
        yield from future.result()

    # No need to executor.shutdown() the executor at this point, it'd be an unwatned code line
    print("End: retrieved results")
