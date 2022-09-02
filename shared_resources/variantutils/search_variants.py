import threading
import hashlib
import jsons
from uuid import uuid4
import time

import boto3

from .local_utils import split_query, get_split_query_fan_out
from utils.chrom_matching import get_matching_chromosome
from dynamodb.variant_queries import VariantQuery, VariantResponse
from payloads.lambda_payloads import SplitQueryPayload
from payloads.lambda_responses import PerformQueryResponse

REQUEST_TIMEOUT = 10  # seconds

dynamodb = boto3.client('dynamodb')
aws_lambda = boto3.client('lambda')
s3 = boto3.client('s3')


def perform_variant_search(*,
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
        passthrough=dict()
):
    # get vcf file and the name of chromosome in it eg: "chr1", "Chr4", "CHR1" or just "1"
    vcf_chromosomes = {vcfm.vcf: get_matching_chromosome(
        vcfm.chromosomes, referenceName) for dataset in datasets for vcfm in dataset.vcfChromosomeMap}

    if len(start) == 2:
        start_min, start_max = start
    else:
        start_min = start_max = start[0]
    if len(end) == 2:
        end_min, end_max = start
    else:
        end_min = end_max = end[0]
    start_min += 1
    start_max += 1
    end_min += 1
    end_max += 1

    if referenceBases != 'N':
        # For specific reference bases region may be smaller
        max_offset = len(referenceBases) - 1
        end_max = min(start_max + max_offset, end_max)
        start_min = max(end_min - max_offset, start_min)
        if end_min > end_max or start_min > start_max:
            # Region search will find nothing, search a dummy region
            start_min = 2000000000
            start_max = start_min
            end_min = start_min + max_offset
            end_max = end_min
    # threading
    threads = []
    query_id = uuid4().hex

    # TODO define variant id and fix; currently consider variant id to be from a unique vcf, chrom, pos, typ
    # TODO optimise this further dataset_id -> vcfs -> vcf_id (do not use vcf index as additions and removals with
    # make the indices inconsistent between requests)
    vcf_dataset_uuid = dict()
    dataset_variant_groups = dict()

    # record the query event on DB
    query_record = VariantQuery(query_id)
    query_record.save()
    split_query_fan_out = get_split_query_fan_out(start_min, start_max)

    # parallelism across datasets
    for dataset in datasets:
        vcf_locations = {
            vcf: vcf_chromosomes[vcf]
            for vcf in dataset.vcfLocations
            if vcf_chromosomes[vcf]
        }

        vcf_dataset_uuid.update(
            {vcf: f"{dataset.id}\t{hashlib.md5(vcf.encode()).hexdigest()}" for vcf in dataset.vcfLocations})
        # record vcf grouping information using the relevant vcf files
        vcf_groups = [
            grp for grp in [
                [loc for loc in vcfg if loc in vcf_locations]
                for vcfg in dataset.vcfGroups
            ]
            if len(grp) > 0
        ]
        # vcf groups being searched for
        dataset_variant_groups[dataset.id] = vcf_groups

        # record perform query fan out size
        perform_query_fan_out = split_query_fan_out * len(vcf_locations)
        query_record.update(actions=[
            VariantQuery.fanOut.set(
                query_record.fanOut + perform_query_fan_out)
        ])

        # call split query for each dataset found
        payload = SplitQueryPayload(
            passthrough=passthrough,
            dataset_id=dataset.id,
            query_id=query_id,
            vcf_locations=vcf_locations,
            vcf_groups=vcf_groups,
            reference_bases=referenceBases,
            region_start=start_min,
            region_end=start_max,
            end_min=end_min,
            end_max=end_max,
            alternate_bases=alternateBases,
            variant_type=variantType,
            include_datasets=includeResultsetResponses,
            requested_granularity=requestedGranularity,
            variant_min_length=variantMinLength,
            variant_max_length=variantMaxLength
        )
        thread = threading.Thread(
            target=split_query,
            kwargs={'payload': payload}
        )
        thread.start()
        threads.append(thread)

    exists = False

    # wait while all the threads complete
    for thread in threads:
        thread.join()

    start_time = time.time()
    query_results = dict()
    last_read_position = 0

    while time.time() - start_time < REQUEST_TIMEOUT:
        try:
            for item in VariantResponse.variantResponseIndex.query(query_id, VariantResponse.responseNumber > last_read_position):
                query_results[item.responseNumber] = item.responseLocation
                last_read_position = item.responseNumber
            query_record.refresh()
            if query_record.fanOut == 0:
                print("Query fan in completed")
                break
        except:
            print("Errored")
            break
        time.sleep(1)

    query_responses = []

    for _, loc in query_results.items():
        print(loc.bucket, loc.key)
        obj = s3.get_object(
            Bucket=loc.bucket,
            Key=loc.key,
        )
        query_response = jsons.loads(obj['Body'].read(), PerformQueryResponse)
        exists = exists or query_response.exists

        if requestedGranularity == 'boolean' and exists:
            return True, []
        
        query_responses.append(query_response)

    if requestedGranularity == 'boolean':
        return exists, []

    return exists, query_responses
