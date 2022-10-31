from collections import defaultdict
import json
import os
import base64

from variantutils.search_variants import perform_variant_search
from apiutils.api_response import bundle_response, fetch_from_cache
import apiutils.responses as responses
import apiutils.entries as entries
from athena.dataset import get_all_datasets
from dynamodb.variant_queries import get_job_status, JobStatus, VariantQuery, get_current_time_utc


BEACON_API_VERSION = os.environ['BEACON_API_VERSION']


def route(event, query_id):
    if event['httpMethod'] == 'GET':
        params = event['queryStringParameters'] or dict()
        print(f"Query params {params}")
        apiVersion = params.get("apiVersion", BEACON_API_VERSION)
        requestedSchemas = params.get("requestedSchemas", [])
        skip = params.get("skip", 0)
        limit = params.get("limit", 100)
        includeResultsetResponses = params.get("includeResultsetResponses", 'NONE')
        start = params.get("start", [])
        end = params.get("end", [])
        assemblyId = params.get("assemblyId", None)
        referenceName = params.get("referenceName", None)
        referenceBases = params.get("referenceBases", None)
        alternateBases = params.get("alternateBases", None)
        variantMinLength = params.get("variantMinLength", 0)
        variantMaxLength = params.get("variantMaxLength", -1)
        variantType = params.get("variantType", None)
        allele = params.get("allele", None)
        geneid = params.get("geneid", None)
        aminoacidchange = params.get("aminoacidchange", None)
        filters = params.get("filters", [])
        requestedGranularity = params.get("requestedGranularity", "boolean")

    if event['httpMethod'] == 'POST':
        params = json.loads(event['body']) or dict()
        print(f"POST params {params}")
        meta = params.get("meta", dict())
        query = params.get("query", dict()) or dict()
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

    if len(filters) > 0:
        # supporting ontology terms
        pass
        
    check_all = includeResultsetResponses in ('HIT', 'ALL')
    status = get_job_status(query_id)

    if status == JobStatus.NEW:
        datasets = get_all_datasets(assemblyId)
        query_responses = perform_variant_search(
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
            query_id=query_id
        )
    
        variants = set()
        results = list()
        found = set()
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

                        if internal_id not in found:
                            results.append(entries.get_variant_entry(base64.b64encode(f'{internal_id}'.encode()).decode(), assemblyId, ref, alt, int(pos), int(pos) + len(alt), typ))
                            found.add(internal_id)

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
                reqPagination=responses.get_pagination_object(skip, limit),
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
    event = {
        "resource": "/g_variants",
        "path": "/g_variants",
        "httpMethod": "POST",
        "body": json.dumps(
            {
                "meta": {
                    "apiVersion": "v2.0"
                },
                "query": {
                    "pagination": {
                        "limit": 100,
                        "skip": 0
                    },
                    "includeResultsetResponses": "HIT",
                    "requestedGranularity": "record",
                    "requestParameters": {
                        "assemblyId": "GRCH38",
                        "start": [
                            10000000
                        ],
                        "end": [
                            10010100
                        ],
                        "referenceBases": "A",
                        "referenceName": "5",
                        "alternateBases": "N"
                    }
                }
            })
        }
    route(event, '36551e7a54877bdf0c8ea8938ab40ff5')