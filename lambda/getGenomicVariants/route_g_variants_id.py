from collections import defaultdict
import json
import os
import base64

from apiutils.api_response import bundle_response, fetch_from_cache
from variantutils.search_variants import perform_variant_search
from athena.dataset import get_datasets
import apiutils.responses as responses
import apiutils.entries as entries
from dynamodb.variant_queries import get_job_status, JobStatus, VariantQuery, get_current_time_utc


BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']


def route(event, query_id):
    if event['httpMethod'] == 'GET':
        params = event.get('queryStringParameters', dict()) or dict()
        print(f"Query params {params}")
        apiVersion = params.get("apiVersion", BEACON_API_VERSION)
        requestedSchemas = params.get("requestedSchemas", [])
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

    variant_id = event["pathParameters"].get("id", None)
    
    dataset_hash = base64.b64decode(variant_id.encode()).decode()
    assemblyId, referenceName, pos, referenceBases, alternateBases = dataset_hash.split('\t')
    pos = int(pos) - 1
    start = [pos]
    end = [pos + len(alternateBases)]
    status = get_job_status(query_id) 
    
    if status == JobStatus.NEW:
        datasets = get_datasets(assemblyId, skip=0, limit='ALL')
        variants = set()
        results = list()
        # key=pos-ref-alt
        # val=counts
        variant_call_counts = defaultdict(int)
        variant_allele_counts = defaultdict(int)

        query_responses = perform_variant_search(
            datasets=datasets,
            referenceName=referenceName,
            referenceBases=referenceBases,
            alternateBases=alternateBases,
            start=start,
            end=end,
            variantType=None,
            variantMinLength=0,
            variantMaxLength=-1,
            requestedGranularity=requestedGranularity,
            includeResultsetResponses='ALL',
            query_id=query_id
        )

        exists = False

        for query_response in query_responses:
            exists = exists or query_response.exists

            if exists:
                if requestedGranularity == 'boolean':
                    break
                variants.update(query_response.variants)

                for variant in query_response.variants:
                    chrom, pos, ref, alt, typ = variant.split('\t')
                    idx = f'{pos}_{ref}_{alt}'
                    variant_call_counts[idx] += query_response.call_count
                    variant_allele_counts[idx] += query_response.all_alleles_count
                    internal_id = f'{assemblyId}\t{chrom}\t{pos}\t{ref}\t{alt}'
                    results.append(entries.get_variant_entry(base64.b64encode(f'{internal_id}'.encode()).decode(), assemblyId, ref, alt, int(pos), int(pos) + len(alt), typ))

        query = VariantQuery.get(query_id)
        query.update(actions=[
            VariantQuery.complete.set(True), 
            VariantQuery.elapsedTime.set((get_current_time_utc() - query.startTime).total_seconds())
        ])

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