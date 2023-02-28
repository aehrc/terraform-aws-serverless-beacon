from collections import defaultdict
import json
import queue
import threading
import os
import base64
import jsons


from apiutils.api_response import bundle_response, fetch_from_cache
from variantutils.search_variants import perform_variant_search_sync
import apiutils.responses as responses
from athena.biosample import Biosample
from dynamodb.variant_queries import get_job_status, JobStatus, VariantQuery, get_current_time_utc
from athena.dataset import Dataset, parse_datasets_with_samples
from athena.common import entity_search_conditions, run_custom_query

from athena.filter_functions import new_entity_search_conditions

BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BIOSAMPLES_TABLE = os.environ['BIOSAMPLES_TABLE']
DATASETS_TABLE = os.environ['DATASETS_TABLE']
ANALYSES_TABLE = os.environ['ANALYSES_TABLE']
METADATA_DATABASE = os.environ['METADATA_DATABASE']
METADATA_BUCKET = os.environ['METADATA_BUCKET']


def datasets_query(conditions, assembly_id):
    query = f'''
    SELECT D.id, D._vcflocations, D._vcfchromosomemap, ARRAY_AGG(A._vcfsampleid) as samples
    FROM "{METADATA_DATABASE}"."{ANALYSES_TABLE}" A
    JOIN "{METADATA_DATABASE}"."{DATASETS_TABLE}" D
    ON A._datasetid = D.id
    {conditions} 
    AND D._assemblyid='{assembly_id}' 
    GROUP BY D.id, D._vcflocations, D._vcfchromosomemap 
    '''
    return query


def datasets_query_fast(assembly_id):
    query = f'''
    SELECT id, _vcflocations, _vcfchromosomemap
    FROM "{METADATA_DATABASE}"."{DATASETS_TABLE}"
    WHERE _assemblyid='{assembly_id}' 
    '''
    return query


def get_count_query(dataset_id, sample_names):
    query = f'''
    SELECT COUNT(id)
    FROM 
        "{{database}}"."{BIOSAMPLES_TABLE}" JOIN "{{database}}"."{ANALYSES_TABLE}"
    ON 
        "{{database}}"."{ANALYSES_TABLE}".biosampleid
        =
        "{{database}}"."{BIOSAMPLES_TABLE}".id
    WHERE 
            "{{database}}"."{ANALYSES_TABLE}"._datasetid='{dataset_id}'
        AND 
            "{{database}}"."{BIOSAMPLES_TABLE}"._datasetid='{dataset_id}'
        AND
            "{{database}}"."{ANALYSES_TABLE}"._vcfsampleid
        IN 
            ({','.join([f"'{sn}'" for sn in sample_names])})
    '''
    return query


def get_bool_query(dataset_id, sample_names):
    query = f'''
    SELECT 1
    FROM 
        "{{database}}"."{BIOSAMPLES_TABLE}" JOIN "{{database}}"."{ANALYSES_TABLE}"
    ON 
        "{{database}}"."{ANALYSES_TABLE}".biosampleid
        =
        "{{database}}"."{BIOSAMPLES_TABLE}".id
    WHERE 
            "{{database}}"."{ANALYSES_TABLE}"._datasetid='{dataset_id}'
        AND 
            "{{database}}"."{BIOSAMPLES_TABLE}"._datasetid='{dataset_id}'
        AND
            "{{database}}"."{ANALYSES_TABLE}"._vcfsampleid
        IN 
            ({','.join([f"'{sn}'" for sn in sample_names])})
    LIMIT 1
    '''
    return query


# TODO break into many queries (ATHENA SQL LIMIT)
# https://docs.aws.amazon.com/athena/latest/ug/service-limits.html
def get_record_query(dataset_id, sample_names):
    query = f'''
    SELECT "{{database}}"."{BIOSAMPLES_TABLE}".* 
    FROM 
        "{{database}}"."{BIOSAMPLES_TABLE}" JOIN "{{database}}"."{ANALYSES_TABLE}"
    ON 
        "{{database}}"."{ANALYSES_TABLE}".biosampleid
        =
        "{{database}}"."{BIOSAMPLES_TABLE}".id
    WHERE 
            "{{database}}"."{ANALYSES_TABLE}"._datasetid='{dataset_id}'
        AND 
            "{{database}}"."{BIOSAMPLES_TABLE}"._datasetid='{dataset_id}'
        AND
            "{{database}}"."{ANALYSES_TABLE}"._vcfsampleid
        IN 
            ({','.join([f"'{sn}'" for sn in sample_names])})
    '''
    return query


def route(event, query_id):
    if event['httpMethod'] == 'GET':
        params = event.get('queryStringParameters', dict()) or dict()
        print(f"Query params {params}")
        apiVersion = params.get("apiVersion", BEACON_API_VERSION)
        requestedSchemas = params.get("requestedSchemas", [])
        requestedGranularity = params.get("requestedGranularity", "boolean")
        skip = params.get("skip", 0)
        limit = params.get("limit", 100)
        # currentPage = params.get("currentPage", None)
        filters_list = []
        filters_str = params.get("filters", filters_list)
        if isinstance(filters_str, str):
            filters_list = filters_str.split(',')
        filters = [{'id': fil_id} for fil_id in filters_list]

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
        # pagination
        pagination = query.get("pagination", dict())
        skip = pagination.get("skip", 0)
        limit = pagination.get("limit", 100)
        # currentPage = pagination.get("currentPage", None)
        # previousPage = pagination.get("previousPage", None)
        nextPage = pagination.get("nextPage", None)
        filters = query.get("filters", [])
        requestParameters = query.get("requestParameters", dict())

    variant_id = event["pathParameters"].get("id", None)
    
    dataset_hash = base64.b64decode(variant_id.encode()).decode()
    assemblyId, referenceName, pos, referenceBases, alternateBases = dataset_hash.split('\t')
    pos = int(pos) - 1
    start = [pos]
    end = [pos + len(alternateBases)]
    status = get_job_status(query_id) 
    dataset_samples = defaultdict(set)

    if status == JobStatus.NEW:
        conditions, execution_parameters = new_entity_search_conditions(filters, 'analyses', 'biosamples', id_modifier='A.id')

        if conditions:
            query = datasets_query(conditions, assemblyId)
            exec_id = run_custom_query(query, return_id=True, execution_parameters=execution_parameters)
            datasets, samples = parse_datasets_with_samples(exec_id)
        else:
            query = datasets_query_fast(assemblyId)
            datasets = Dataset.get_by_query(query, execution_parameters=execution_parameters)
            samples = []

        query_responses = perform_variant_search_sync(
            datasets=datasets,
            referenceName=referenceName,
            referenceBases=referenceBases,
            alternateBases=alternateBases,
            start=start,
            end=end,
            variantType=None,
            variantMinLength=0,
            variantMaxLength=-1,
            requestedGranularity='record', # we need the records for this task
            includeResultsetResponses='ALL',
            query_id=query_id,
            dataset_samples=samples,
            passthrough={ 'includeSamples': True }
        )

        exists = False

        for query_response in query_responses:
            exists = exists or query_response.exists
            
            if query_response.exists:
                if requestedGranularity == 'boolean':
                    break
                dataset_samples[query_response.dataset_id].update(sorted(query_response.sample_names))

        queries = []
        iterated_biosamples = 0
        chosen_biosamples = 0

        for dataset_id, sample_names in dataset_samples.items():
            if (len(sample_names)) > 0:
                if requestedGranularity == 'count':
                    # query = get_count_query(dataset_id, sample_names)
                    # queries.append(query)
                    # TODO optimise for duplicate individuals
                    iterated_biosamples += len(sample_names)
                elif requestedGranularity in ('record', 'aggregated'):
                    # TODO optimise for duplicate individuals
                    chosen_samples = []
                    
                    for sample_name in sample_names:
                        iterated_biosamples += 1
                        if iterated_biosamples > skip and chosen_biosamples < limit:
                            chosen_samples.append(sample_name)
                            chosen_biosamples += 1
                            
                        if chosen_biosamples == limit:
                            break
                    if len(chosen_samples) > 0:
                        query = get_record_query(dataset_id, chosen_samples)
                        queries.append(query)

        # query = VariantQuery.get(query_id)
        # query.update(actions=[
        #     VariantQuery.complete.set(True), 
        #     VariantQuery.elapsedTime.set((get_current_time_utc() - query.startTime).total_seconds())
        # ])

        if requestedGranularity == 'boolean':
            response = responses.get_boolean_response(exists=exists)
            print('Returning Response: {}'.format(json.dumps(response)))
            return bundle_response(200, response, query_id)

        if requestedGranularity == 'count':
            count = iterated_biosamples
            response = responses.get_counts_response(exists=count > 0, count=count)
            print('Returning Response: {}'.format(json.dumps(response)))
            return bundle_response(200, response, query_id)

        if requestedGranularity in ('record', 'aggregated'):
            query = ' UNION '.join(queries)
            biosamples = Biosample.get_by_query(query) if len(queries) > 0 else []
            response = responses.get_result_sets_response(
                setType='biosamples', 
                reqPagination=responses.get_pagination_object(skip=skip, limit=limit),
                exists=len(biosamples) > 0,
                total=len(biosamples),
                results=jsons.dump(biosamples, strip_privates=True)
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
