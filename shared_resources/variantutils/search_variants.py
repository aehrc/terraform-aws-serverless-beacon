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
    try:
        # get vcf file and the name of chromosome in it eg: "chr1", "Chr4", "CHR1" or just "1"
        vcf_chromosomes = {vcfm['vcf']: get_matching_chromosome(
            vcfm['chromosomes'], referenceName) for dataset in datasets for vcfm in dataset._vcfChromosomeMap}

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
        print('Error occured ', e)
        return False, []

    start_min += 1
    start_max += 1
    end_min += 1
    end_max += 1

    # threading
    threads = []
    query_id = uuid4().hex

    # record the query event on DB
    query_record = VariantQuery(query_id)
    query_record.save()
    split_query_fan_out = get_split_query_fan_out(start_min, start_max)
    perform_query_fan_out = 0

    # parallelism across datasets
    for dataset in datasets:
        vcf_locations = {
            vcf: vcf_chromosomes[vcf]
            for vcf in dataset._vcfLocations
            if vcf_chromosomes[vcf]
        }

        # record perform query fan out size
        perform_query_fan_out += split_query_fan_out * len(vcf_locations)

        # call split query for each dataset found
        payload = SplitQueryPayload(
            passthrough=passthrough,
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
            variant_max_length=variantMaxLength
        )
        thread = threading.Thread(
            target=split_query,
            kwargs={'payload': payload}
        )
        thread.start()
        threads.append(thread)

    query_record.update(actions=[
        VariantQuery.fanOut.set(
            VariantQuery.fanOut + perform_query_fan_out)
    ])

    exists = False

    # wait while all the threads complete
    for thread in threads:
        thread.join()

    start_time = time.time()
    query_results = dict()

    while time.time() - start_time < REQUEST_TIMEOUT:
        try:
            query_record.refresh()
            time.sleep(0.5)
            if query_record.fanOut == 0:
                for item in  VariantResponse.batch_get([(query_id, resp_no) for resp_no in range(1, query_record.responses + 1)]):
                    print('RECEIVED:', item.to_json())
                    query_results[item.responseNumber] = item
                print("Query fan in completed")
                break
        except Exception as e:
            print("Errored", e)
            break

    query_responses = []

    for _, var_response in query_results.items():
        if var_response.checkS3:
            loc = var_response.responseLocation
            obj = s3.get_object(
                Bucket=loc.bucket,
                Key=loc.key,
            )
            query_response = jsons.loads(obj['Body'].read(), PerformQueryResponse)
        else:
            query_response = jsons.loads(var_response.result, PerformQueryResponse)

        exists = exists or query_response.exists

        if requestedGranularity == 'boolean' and not exists:
            return True, []
        
        query_responses.append(query_response)

    if requestedGranularity == 'boolean':
        return exists, []

    return exists, query_responses
