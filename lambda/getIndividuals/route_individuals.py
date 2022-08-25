from collections import defaultdict
import json
import jsonschema
import queue
import threading
import os
import hashlib
import base64
import jsons
from uuid import uuid4
import time

import boto3

from dynamodb.variant_queries import VariantQuery, VariantResponse
from dynamodb.datasets import Dataset
from local_utils import split_query, get_split_query_fan_out
from apiutils.api_response import bundle_response, bad_request
from utils.chrom_matching import get_matching_chromosome
import apiutils.responses as responses
import apiutils.entries as entries
from payloads.lambda_payloads import SplitQueryPayload
from payloads.lambda_responses import PerformQueryResponse


SPLIT_SIZE = 1000000
BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']
SPLIT_QUERY = os.environ['SPLIT_QUERY_LAMBDA']
REQUEST_TIMEOUT = 10 # seconds 

dynamodb = boto3.client('dynamodb')
aws_lambda = boto3.client('lambda')
s3 = boto3.client('s3')
requestSchemaJSON = json.load(open("requestParameters.json"))


def get_datasets(assembly_id, dataset_ids=None):
    items = []
    for item in Dataset.datasetIndex.query(assembly_id):
        items.append(item)
    # TODO support more advanced querying
    if dataset_ids:
        items = [i for i in items if i.id in dataset_ids]
    return items


def route(event):
    if (event['httpMethod'] == 'GET'):
        params = event['queryStringParameters']
        print(f"Query params {params}")
        apiVersion = params.get("apiVersion", BEACON_API_VERSION)
        requestedSchemas = params.get("requestedSchemas", [])
        skip = params.get("skip", None)
        limit = params.get("limit", None)
        includeResultsetResponses = params.get("includeResultsetResponses", 'NONE')
        start = params.get("start", None)
        end = params.get("end", None)
        assemblyId = params.get("assemblyId", None)
        referenceName = params.get("referenceName", None)
        referenceBases = params.get("referenceBases", None)
        alternateBases = params.get("alternateBases", None)
        variantMinLength = params.get("variantMinLength", 0)
        variantMaxLength = params.get("variantMaxLength", -1)
        allele = params.get("allele", None)
        geneid = params.get("geneid", None)
        aminoacidchange = params.get("aminoacidchange", None)
        filters = params.get("filters", [])
        requestedGranularity = params.get("requestedGranularity", "boolean")

    if (event['httpMethod'] == 'POST'):
        params = json.loads(event['body'])
        print(f"POST params {params}")
        meta = params.get("meta", dict())
        query = params.get("query", dict())
        # meta data
        apiVersion = meta.get("apiVersion", BEACON_API_VERSION)
        requestedSchemas = meta.get("requestedSchemas", [])
        # query data
        requestParameters = query.get("requestParameters", None)
        requestedGranularity = query.get("requestedGranularity", "boolean")
        # pagination
        pagination = query.get("pagination", dict())
        skip = pagination.get("skip", 0)
        limit = pagination.get("limit", 100)
        currentPage = pagination.get("currentPage", None)
        previousPage = pagination.get("previousPage", None)
        nextPage = pagination.get("nextPage", None)
        # query request params
        requestParameters = query.get("requestParameters", dict())
        # validate query request
        validator = jsonschema.Draft202012Validator(requestSchemaJSON['g_variant'])
        # print(validator.schema)
        if errors := sorted(validator.iter_errors(requestParameters), key=lambda e: e.path):
            return bad_request(errorMessage= "\n".join([error.message for error in errors]))
            # raise error
        start = requestParameters.get("start", None)
        end = requestParameters.get("end", None)
        assemblyId = requestParameters.get("assemblyId", None)
        referenceName = requestParameters.get("referenceName", None)
        referenceBases = requestParameters.get("referenceBases", None)
        alternateBases = requestParameters.get("alternateBases", None)
        variantMinLength = requestParameters.get("variantMinLength", 0)
        variantMaxLength = requestParameters.get("variantMaxLength", -1)
        allele = requestParameters.get("allele", None)
        geneId = requestParameters.get("geneId", None)
        aminoacidChange = requestParameters.get("aminoacidChange", None)
        filters = requestParameters.get("filters", [])
        variantType = requestParameters.get("variantType", None)
        includeResultsetResponses = requestParameters.get("includeResultsetResponses", 'NONE')

    if len(filters) > 0:
        # supporting ontology terms
        pass
        
    datasets = get_datasets(assemblyId)
    # get vcf file and the name of chromosome in it eg: "chr1", "Chr4", "CHR1" or just "1"
    vcf_chromosomes = { vcfm.vcf: get_matching_chromosome(vcfm.chromosomes, referenceName) for dataset in datasets for vcfm in dataset.vcfChromosomeMap }
    check_all = includeResultsetResponses in ('HIT', 'ALL')

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
    thread_responses = queue.Queue()
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
        
        vcf_dataset_uuid.update({ vcf: f"{dataset.id}\t{hashlib.md5(vcf.encode()).hexdigest()}" for vcf in dataset.vcfLocations })
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
            VariantQuery.fanOut.set(query_record.fanOut + perform_query_fan_out)
        ])

        # call split query for each dataset found
        payload = SplitQueryPayload(
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
                kwargs={ 'payload': payload }
            )
        thread.start()
        threads.append(thread)

    exists = False
    variants = set()
    results = list()
    dataset_vcf_group_map = dict()

    # dict of key dataset.id and value=dict with key=vcf val=groupId
    for k, vgs in dataset_variant_groups.items():
        dataset_vcf_group_map[k] = { v : n for n, vg in enumerate(vgs) for v in vg }

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

    # key=pos-ref-alt
    # val=counts
    variant_call_counts = defaultdict(int)
    variant_allele_counts = defaultdict(int)
    
    for _, loc in query_results.items():
        print(loc.bucket, loc.key)
        obj = s3.get_object(
            Bucket=loc.bucket,
            Key=loc.key,
        )
        query_response = jsons.loads(obj['Body'].read(), PerformQueryResponse)
        exists = exists or query_response.exists

        # immediately return the boolean response if exists
        if requestedGranularity == 'boolean' and exists:
            response = responses.get_boolean_response(exists=exists)
            print('Returning Response: {}'.format(json.dumps(response)))
            return bundle_response(200, response)
        else:
            exists = exists or query_response.exists
            if exists:
                exists = True
                if check_all:
                    variants.update(query_response.variants)

                    for variant in query_response.variants:
                        chrom, pos, ref, alt, typ = variant.split('\t')
                        idx = f'{pos}_{ref}_{alt}'
                        variant_call_counts[idx] += query_response.call_count
                        variant_allele_counts[idx] += query_response.all_alleles_count
                        internal_id = f'{assemblyId}\t{chrom}\t{pos}\t{ref}\t{alt}'
                        results.append(entries.get_variant_entry(base64.b64encode(f'{internal_id}'.encode()).decode(), assemblyId, ref, alt, int(pos), int(pos) + len(alt), typ))

    if requestedGranularity == 'boolean':
        response = responses.get_boolean_response(exists=exists)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if requestedGranularity == 'count':
        response = responses.get_counts_response(exists=exists, count=len(variants))
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if requestedGranularity in ('record', 'aggregated'):
        response = responses.get_result_sets_response(
            setType='genomicVariant', 
            exists=exists,
            total=len(variants),
            results=results
        )
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)
