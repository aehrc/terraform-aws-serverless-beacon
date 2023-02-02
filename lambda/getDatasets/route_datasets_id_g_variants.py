from collections import defaultdict
import json
import os
import base64
import csv

from smart_open import open as sopen

from apiutils.api_response import bundle_response, fetch_from_cache
from variantutils.search_variants import perform_variant_search, perform_variant_search_sync
import apiutils.responses as responses
import apiutils.entries as entries
from athena.dataset import Dataset, parse_datasets_with_samples
from dynamodb.variant_queries import get_job_status, JobStatus, VariantQuery, get_current_time_utc
from athena.common import entity_search_conditions, run_custom_query

from athena.filter_functions import new_entity_search_conditions

BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
ANALYSES_TABLE = os.environ['ANALYSES_TABLE']
METADATA_DATABASE = os.environ['METADATA_DATABASE']
DATASETS_TABLE = os.environ['DATASETS_TABLE']
METADATA_BUCKET = os.environ['METADATA_BUCKET']


def datasets_query(conditions, assembly_id, dataset_id):
    query = f'''
    SELECT D.id, D._vcflocations, D._vcfchromosomemap, ARRAY_AGG(A._vcfsampleid) as samples
    FROM "{METADATA_DATABASE}"."{ANALYSES_TABLE}" A
    JOIN "{METADATA_DATABASE}"."{DATASETS_TABLE}" D
    ON A._datasetid = D.id
    {conditions} 
    AND D._assemblyid='{assembly_id}' 
    AND D.id='{dataset_id}'
    GROUP BY D.id, D._vcflocations, D._vcfchromosomemap 
    '''
    return query


def datasets_query_fast(assembly_id, dataset_id):
    query = f'''
    SELECT id, _vcflocations, _vcfchromosomemap
    FROM "{METADATA_DATABASE}"."{DATASETS_TABLE}"
    WHERE _assemblyid='{assembly_id}' 
    AND id='{dataset_id}'
    '''
    return query


def route(event, query_id):
    if event['httpMethod'] == 'GET':
        params = event.get('queryStringParameters', dict()) or dict()
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
        filters_list = []
        filters_str = params.get("filters", filters_list)
        if isinstance(filters_str, str):
            filters_list = filters_str.split(',')
        filters = [{'id': fil_id} for fil_id in filters_list]
        requestedGranularity = params.get("requestedGranularity", "boolean")

    if event['httpMethod'] == 'POST':
        params = json.loads(event.get('body', "{}")) or dict()
        print(f"POST params {params}")
        meta = params.get("meta", dict())
        query = params.get("query", dict())
        # meta data
        apiVersion = meta.get("apiVersion", BEACON_API_VERSION)
        requestedSchemas = meta.get("requestedSchemas", [])
        # query data
        requestedGranularity = query.get("requestedGranularity", "boolean")
        requestParameters = query.get("requestParameters", dict())
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
        filters = query.get("filters", [])
        variantType = requestParameters.get("variantType", None)
        includeResultsetResponses = query.get("includeResultsetResponses", 'NONE')
    
    check_all = includeResultsetResponses in ('HIT', 'ALL')
    dataset_id = event["pathParameters"].get("id", None)
    status = get_job_status(query_id)
    
    if status == JobStatus.NEW:
        conditions, execution_parameters = new_entity_search_conditions(filters, 'analyses', 'datasets', id_modifier='A.id')
        
        if conditions:
            query = datasets_query(conditions, assemblyId, dataset_id)
            exec_id = run_custom_query(query, return_id=True, execution_parameters=execution_parameters)
            datasets, samples = parse_datasets_with_samples(exec_id)
        else:
            query = datasets_query_fast(assemblyId, dataset_id)
            datasets = Dataset.get_by_query(query, execution_parameters=execution_parameters)
            samples = []

        query_responses = perform_variant_search_sync(
            datasets=datasets,
            referenceName=referenceName,
            referenceBases=referenceBases,
            alternateBases=alternateBases,
            start=start,
            end=end,
            variantType=variantType,
            variantMinLength=variantMinLength,
            variantMaxLength=variantMaxLength,
            requestedGranularity=requestedGranularity,
            includeResultsetResponses=includeResultsetResponses,
            query_id=query_id,
            dataset_samples=samples
        )

        variants = set()
        results = list()
        # key=pos-ref-alt
        # val=counts
        variant_call_counts = defaultdict(int)
        variant_allele_counts = defaultdict(int)
        exists = False

        for query_response in query_responses:
            exists = exists or query_response.exists

            if exists:
                if requestedGranularity == 'boolean':
                    break
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
            return bundle_response(200, response, query_id)

        if requestedGranularity == 'count':
            response = responses.get_counts_response(exists=exists, count=len(variants))
            print('Returning Response: {}'.format(json.dumps(response)))
            return bundle_response(200, response, query_id)

        if requestedGranularity in ('record', 'aggregated'):
            response = responses.get_result_sets_response(
                setType='genomicVariant', 
                exists=exists,
                total=len(variants),
                results=results
            )
            print('Returning Response: {}'.format(json.dumps(response)))
            return bundle_response(200, response, query_id)

    elif status == JobStatus.RUNNING:
        response = responses.get_boolean_response(exists=False, info={'message': 'Query still running.'})
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)
    else:
        response = fetch_from_cache(query_id)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)


if __name__ == '__main__':
    pass
