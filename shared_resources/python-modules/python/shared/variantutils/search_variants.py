import concurrent.futures
import time
import copy
import queue

import jsons
import botocore
import boto3

from .local_utils import split_query, split_query_sync, get_split_query_fan_out
from shared.utils.chrom_matching import get_matching_chromosome
from shared.dynamodb.variant_queries import VariantQuery, VariantResponse
from shared.payloads.lambda_payloads import SplitQueryPayload
from shared.payloads.lambda_responses import PerformQueryResponse


REQUEST_TIMEOUT = 600  # seconds
THREADS = 500

client_config = botocore.config.Config(
    max_pool_connections=100,
)
aws_lambda = boto3.client("lambda", config=client_config)
s3 = boto3.client("s3")


def perform_variant_search(
    *,
    datasets,
    referenceName,
    referenceBases,
    alternateBases,
    start,
    end,
    variantType,
    variantMinLength,
    variantMaxLength,
    requestedGranularity,
    includeResultsetResponses,
    query_id="TEST",
    passthrough=dict(),
    dataset_samples=[],
):
    try:
        # get vcf file and the name of chromosome in it eg: "chr1", "Chr4", "CHR1" or just "1"
        vcf_chromosomes = {
            vcfm["vcf"]: get_matching_chromosome(vcfm["chromosomes"], referenceName)
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

    # record the query event on DB
    query_record = VariantQuery(query_id)
    query_record.save()
    split_query_fan_out = get_split_query_fan_out(start_min, start_max)
    perform_query_fan_out = 0

    print("Start event publishing")
    pool = concurrent.futures.ThreadPoolExecutor(THREADS)

    # parallelism across datasets
    for n, dataset in enumerate(datasets):
        vcf_locations = {
            vcf: vcf_chromosomes[vcf]
            for vcf in dataset._vcfLocations
            if vcf_chromosomes[vcf]
        }

        event_passthrough = copy.deepcopy(passthrough)

        # adjust event passthrough if needed
        if len(dataset_samples) == len(datasets) and len(dataset_samples[n]) > 0:
            event_passthrough["sampleNames"] = dataset_samples[n]
            event_passthrough["selectedSamplesOnly"] = True

        # record perform query fan out size
        perform_query_fan_out += split_query_fan_out * len(vcf_locations)

        # call split query for each dataset found
        payload = SplitQueryPayload(
            passthrough=event_passthrough,
            dataset_id=dataset.id,
            query_id=query_id,
            vcf_locations=vcf_locations,
            vcf_groups=[],
            reference_bases=referenceBases,
            start_min=start_min,
            start_max=start_max,
            end_min=end_min,
            end_max=end_max,
            alternate_bases=alternateBases,
            variant_type=variantType,
            include_datasets=includeResultsetResponses,
            requested_granularity=requestedGranularity,
            variant_min_length=variantMinLength,
            variant_max_length=variantMaxLength,
        )
        pool.submit(split_query, payload)

    pool.shutdown()

    query_record.update(
        actions=[VariantQuery.fanOut.set(VariantQuery.fanOut + perform_query_fan_out)]
    )

    print("End event publishing")

    start_time = time.time()
    query_results = dict()

    while time.time() - start_time < REQUEST_TIMEOUT:
        try:
            query_record.refresh()
            time.sleep(0.5)
            if query_record.fanOut == 0:
                for item in VariantResponse.batch_get(
                    [
                        (query_id, resp_no)
                        for resp_no in range(1, query_record.responses + 1)
                    ]
                ):
                    query_results[item.responseNumber] = item
                print(f"Query fan in completed with {len(query_results)} items")
                break
        except Exception as e:
            print("Errored", e)
            break

    print("Start results generator")
    for _, var_response in query_results.items():
        if var_response.checkS3:
            loc = var_response.responseLocation
            obj = s3.get_object(
                Bucket=loc.bucket,
                Key=loc.key,
            )
            query_response = jsons.loads(obj["Body"].read(), PerformQueryResponse)
        else:
            query_response = jsons.loads(var_response.result, PerformQueryResponse)

        yield query_response


def perform_variant_search_sync(
    *,
    datasets,
    referenceName,
    referenceBases,
    alternateBases,
    start,
    end,
    variantType,
    variantMinLength,
    variantMaxLength,
    requestedGranularity,
    includeResultsetResponses,
    query_id="TEST",
    passthrough=dict(),
    dataset_samples=[],
):
    try:
        # get vcf file and the name of chromosome in it eg: "chr1", "Chr4", "CHR1" or just "1"
        vcf_chromosomes = {
            vcfm["vcf"]: get_matching_chromosome(vcfm["chromosomes"], referenceName)
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

    print("Start event publishing")
    results_queue = queue.Queue()
    pool = concurrent.futures.ThreadPoolExecutor(THREADS)

    # parallelism across datasets
    for n, dataset in enumerate(datasets):
        vcf_locations = {
            vcf: vcf_chromosomes[vcf]
            for vcf in dataset._vcfLocations
            if vcf_chromosomes[vcf]
        }

        event_passthrough = copy.deepcopy(passthrough)

        # adjust event passthrough if needed
        if len(dataset_samples) == len(datasets) and len(dataset_samples[n]) > 0:
            event_passthrough["sampleNames"] = dataset_samples[n]
            event_passthrough["selectedSamplesOnly"] = True

        # call split query for each dataset found
        payload = SplitQueryPayload(
            passthrough=event_passthrough,
            dataset_id=dataset.id,
            query_id=query_id,
            vcf_locations=vcf_locations,
            vcf_groups=[],
            reference_bases=referenceBases,
            start_min=start_min,
            start_max=start_max,
            end_min=end_min,
            end_max=end_max,
            alternate_bases=alternateBases,
            variant_type=variantType,
            include_datasets=includeResultsetResponses,
            requested_granularity=requestedGranularity,
            variant_min_length=variantMinLength,
            variant_max_length=variantMaxLength,
        )
        pool.submit(split_query_sync, payload, results_queue)

    pool.shutdown()
    print("End event publishing")

    return [
        jsons.load(res, PerformQueryResponse)
        for res_array in results_queue.queue
        for res in res_array
    ]
