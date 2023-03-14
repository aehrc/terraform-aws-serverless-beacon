from collections import defaultdict
import json
import os
import base64

from apiutils.api_response import bundle_response
from variantutils.search_variants import perform_variant_search_sync
from athena.common import run_custom_query
from athena.dataset import parse_datasets_with_samples
from athena.filter_functions import new_entity_search_conditions
from apiutils.requests import RequestParams, Granularity, parse_request_params
import apiutils.responses as responses
import apiutils.entries as entries
from apiutils.schemas import DefaultSchemas


ATHENA_METADATA_DATABASE = os.environ['ATHENA_METADATA_DATABASE']
ATHENA_DATASETS_TABLE = os.environ['ATHENA_DATASETS_TABLE']
ATHENA_ANALYSES_TABLE = os.environ['ATHENA_ANALYSES_TABLE']


def datasets_query(conditions, assembly_id, individual_id):
    query = f'''
    SELECT D.id, D._vcflocations, D._vcfchromosomemap, ARRAY_AGG(A._vcfsampleid) as samples
    FROM "{ATHENA_METADATA_DATABASE}"."{ATHENA_ANALYSES_TABLE}" A
    JOIN "{ATHENA_METADATA_DATABASE}"."{ATHENA_DATASETS_TABLE}" D
    ON A._datasetid = D.id
    WHERE A.individualid='{individual_id}'
    AND D._assemblyid='{assembly_id}'
    {(' AND ' + conditions) if len(conditions) > 0 else ''} 
    GROUP BY D.id, D._vcflocations, D._vcfchromosomemap 
    '''
    return query


def route(request: RequestParams, individual_id):
    conditions, execution_parameters = new_entity_search_conditions(
        request.query.filters, 'analyses', 'individuals', id_modifier='A.id', with_where=False)
    query_params = parse_request_params(request)
    query = datasets_query(conditions, query_params.assembly_id, individual_id)
    exec_id = run_custom_query(
        query, return_id=True, execution_parameters=execution_parameters)
    datasets, samples = parse_datasets_with_samples(exec_id)
    check_all = request.query.include_resultset_responses in ('HIT', 'ALL')

    variants = set()
    results = list()
    # key=pos-ref-alt
    # val=counts
    variant_call_counts = defaultdict(int)
    variant_allele_counts = defaultdict(int)
    exists = False

    query_responses = perform_variant_search_sync(
        datasets=datasets,
        referenceName=query_params.reference_name,
        referenceBases=query_params.reference_bases,
        alternateBases=query_params.alternate_bases,
        start=query_params.start,
        end=query_params.end,
        variantType=query_params.variant_type,
        variantMinLength=query_params.variant_min_length,
        variantMaxLength=query_params.variant_max_length,
        requestedGranularity=request.query.requested_granularity,
        includeResultsetResponses=request.query.include_resultset_responses,
        dataset_samples=samples
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
                    internal_id = f'{query_params.assembly_id}\t{chrom}\t{pos}\t{ref}\t{alt}'
                    results.append(entries.get_variant_entry(base64.b64encode(f'{internal_id}'.encode(
                    )).decode(), query_params.assembly_id, ref, alt, int(pos), int(pos) + len(alt), typ))

    if request.query.requested_granularity == 'boolean':
        response = responses.build_beacon_boolean_response(
            {}, 1 if exists else 0, request, {}, DefaultSchemas.GENOMICVARIATIONS)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == 'count':
        response = responses.build_beacon_count_response(
            {}, len(variants), request, {}, DefaultSchemas.GENOMICVARIATIONS)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == Granularity.RECORD:
        response = responses.build_beacon_resultset_response(
            results, len(variants), request, {}, DefaultSchemas.GENOMICVARIATIONS)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)


if __name__ == '__main__':
    pass
