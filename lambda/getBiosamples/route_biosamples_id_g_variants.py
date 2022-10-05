from collections import defaultdict
import json
import os
import base64

from apiutils.api_response import bundle_response
from variantutils.search_variants import perform_variant_search
import apiutils.responses as responses
import apiutils.entries as entries
from athena.analysis import Analysis
from athena.dataset import get_datasets


BEACON_API_VERSION = os.environ['BEACON_API_VERSION']


def get_record_query(id, conditions=[]):
    query = f'''
    SELECT id, _datasetid, _vcfsampleid FROM "{{database}}"."{{table}}"
    WHERE "biosampleid"='{id}'
    {' AND '.join(conditions)}
    '''
    return query


def route(event):
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
        filters = params.get("filters", [])
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
        filters = requestParameters.get("filters", [])
        variantType = requestParameters.get("variantType", None)
        includeResultsetResponses = query.get("includeResultsetResponses", 'NONE')
    
    biosample_id = event["pathParameters"].get("id", None)
    db_results = Analysis.get_by_query(get_record_query(biosample_id))

    # TODO biosample may have multiple run - analyses implement that
    if not len(db_results) > 0:
        response = responses.get_boolean_response(exists=False)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    analysis = db_results[0]
    datasets = get_datasets(assemblyId, dataset_id=analysis._datasetId)
    check_all = includeResultsetResponses in ('HIT', 'ALL')

    variants = set()
    results = list()
    # key=pos-ref-alt
    # val=counts
    variant_call_counts = defaultdict(int)
    variant_allele_counts = defaultdict(int)
    exists, query_responses = perform_variant_search(
        passthrough={
            'selectedSamplesOnly': True,
            'sampleNames': [analysis._vcfSampleId]
        },
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
        includeResultsetResponses=includeResultsetResponses
    )

    for query_response in query_responses:
        exists = exists or query_response.exists

        if exists:
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


if __name__ == '__main__':
    pass
