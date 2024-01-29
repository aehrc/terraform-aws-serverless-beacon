from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Generator, List
import os
import json
import math
import gzip
import base64

import boto3
import jsons

from shared.utils import get_matching_chromosome
from shared.payloads import PerformQueryResponse
from shared.utils import LambdaClient


SPLIT_QUERY_LAMBDA = os.environ["SPLIT_QUERY_LAMBDA"]
SPLIT_SIZE = 20000
THREADS = 200


s3 = boto3.client("s3")
aws_lambda = LambdaClient()


def fan_out(payload: List[dict]):
    # stringified payload
    payload_str = json.dumps(payload)

    # compress if larger than 100 kb
    if len(payload_str) > 100 * 1024:
        payload_str = json.dumps(
            base64.b64encode(gzip.compress(payload_str.encode())).decode()
        )

    response = aws_lambda.invoke(
        FunctionName=SPLIT_QUERY_LAMBDA,
        InvocationType="RequestResponse",
        Payload=payload_str,
    )
    parsed = None
    try:
        parsed = json.loads(response["Payload"].read())
        parsed = jsons.default_list_deserializer(parsed, List[PerformQueryResponse])
    except Exception as e:
        print(parsed, e)
        raise e
    return parsed


def f_cost(N, P):
    return 0.05 * N / P + 0.05 * P


def df_cost(N, P):
    return -0.05 * N / (P**2) + 0.05


# adding scipy will be a huge overhead on lambda layers
# this finds P such that cost is nil
# compared to newton method, this seems a faster alternative
def best_parallelism(N):
    chosen = 1
    best_cost = float("inf")
    # This range must be smaller than total available concurrency
    # otherwise the pipeline will hang without enough lambdas to continue
    # TODO make 800 an env variable
    for P in range(1, 800):
        if (cost := f_cost(N, P)) < best_cost:
            best_cost = cost
            chosen = P

    return chosen


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
) -> Generator[PerformQueryResponse, None, None]:
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
    payloads = []

    # parallelism across datasets
    for n, dataset in enumerate(datasets):
        vcf_locations = {
            vcf: vcf_chromosomes[vcf]
            for vcf in dataset._vcfLocations
            if vcf_chromosomes[vcf]
        }

        split_start = start_min

        while split_start <= start_max:
            # TODO improve SPLIT_SIZE - make dynamic
            split_end = min(split_start + SPLIT_SIZE - 1, start_max)
            for vcf_location, chrom in vcf_locations.items():
                payload = {
                    "query_id": query_id,
                    "dataset_id": dataset.id,
                    "vcf_location": vcf_location,
                    "samples": dataset_samples[n] if dataset_samples else [],
                    "reference_bases": reference_bases or "N",
                    "alternate_bases": alternate_bases or "N",
                    "end_min": end_min,
                    "end_max": end_max,
                    "variant_min_length": variant_min_length,
                    "variant_max_length": variant_max_length,
                    "include_details": include_datasets in ("HIT", "ALL"),
                    "include_samples": include_samples,
                    "region": f"{chrom}:{split_start}-{split_end}",
                    "variant_type": variant_type,
                    "requested_granularity": requested_granularity,
                }
                payloads.append(payload)
            # next split
            split_start += SPLIT_SIZE

    print("Start: event publishing")
    # TODO further split by sample counts to avoid payload overflow
    chunk_size = best_parallelism(len(payloads))
    print(
        f"PAYLOADS - {len(payloads)} CHUNK SIZE - {chunk_size} NO CHUNKS - {math.ceil(len(payloads)/chunk_size)}"
    )
    executor = ThreadPoolExecutor(THREADS)
    futures = [
        executor.submit(fan_out, payloads[itr : itr + chunk_size])
        for itr in range(0, len(payloads), chunk_size)
    ]

    for future in as_completed(futures):
        yield from future.result()

    # No need to executor.shutdown() the executor at this point, it'd be an unwatned code line
    print("End: retrieved results")


if __name__ == "__main__":
    pass
