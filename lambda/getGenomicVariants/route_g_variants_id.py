from collections import defaultdict
import json
import jsonschema
import os
import base64

from apiutils.api_response import bundle_response, bad_request
from variantutils.search_variants import perform_variant_search
from dynamodb.datasets import Dataset
import apiutils.responses as responses
import apiutils.entries as entries


BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']

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
        params = event.get('queryStringParameters', dict()) or dict()
        print(f"Query params {params}")
        apiVersion = params.get("apiVersion", BEACON_API_VERSION)
        requestedSchemas = params.get("requestedSchemas", [])
        requestedGranularity = params.get("requestedGranularity", "boolean")

    if (event['httpMethod'] == 'POST'):
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
        # validate query request
        validator = jsonschema.Draft202012Validator(requestSchemaJSON['g_variant'])
        # print(validator.schema)
        if errors := sorted(validator.iter_errors(requestParameters), key=lambda e: e.path):
            return bad_request(errorMessage= "\n".join([error.message for error in errors]))
            # raise error

    variant_id = event["pathParameters"].get("id", None)
    if variant_id is None:
        return bad_request(errorMessage="Request missing variant ID")
    
    dataset_hash = base64.b64decode(variant_id.encode()).decode()
    assemblyId, referenceName, pos, referenceBases, alternateBases = dataset_hash.split('\t')
    pos = int(pos) - 1
    start = [pos, pos + len(alternateBases)]
    end = [pos, pos + len(alternateBases)]
    
    datasets = get_datasets(assemblyId)
    variants = set()
    results = list()
    # key=pos-ref-alt
    # val=counts
    variant_call_counts = defaultdict(int)
    variant_allele_counts = defaultdict(int)
    includeResultsetResponses = 'ALL'

    exists, query_responses = perform_variant_search(
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
        includeResultsetResponses=includeResultsetResponses
    )

    for query_response in query_responses:
        exists = exists or query_response.exists

        if exists:
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