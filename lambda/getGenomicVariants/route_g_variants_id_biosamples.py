from collections import defaultdict
import json
import queue
import threading
import os
import base64
import jsons


from apiutils.api_response import bundle_response, fetch_from_cache
from variantutils.search_variants import perform_variant_search
import apiutils.responses as responses
from athena.biosample import Biosample
from athena.dataset import get_datasets
from dynamodb.variant_queries import get_job_status, JobStatus, VariantQuery, get_current_time_utc


BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BIOSAMPLES_TABLE = os.environ['BIOSAMPLES_TABLE']
ANALYSES_TABLE = os.environ['ANALYSES_TABLE']


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
def get_record_query(dataset_id, sample_names, skip, limit, conditions=[]):
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
    ORDER BY "{{database}}"."{BIOSAMPLES_TABLE}".id
    OFFSET {skip}
    LIMIT {limit};
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
        filters = [{'id':fil_id} for fil_id in params.get("filters", [])]

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

    variant_id = 'R1JDSDM4CTUJMTAwMDAwMTAJQQlU' # event["pathParameters"].get("id", None)
    
    dataset_hash = base64.b64decode(variant_id.encode()).decode()
    assemblyId, referenceName, pos, referenceBases, alternateBases = dataset_hash.split('\t')
    pos = int(pos) - 1
    start = [pos]
    end = [pos + len(alternateBases)]
    status = get_job_status(query_id) 
    dataset_samples = defaultdict(set)

    if status == JobStatus.NEW:
        datasets = get_datasets(assemblyId, skip=0, limit='ALL')  
        print(datasets)
        query_responses = perform_variant_search(
            passthrough={
                'samplesOnly': True
            },
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
            query_id=query_id
        )

        exists = False

        for query_response in query_responses:
            exists = exists or query_response.exists
            
            if query_response.exists:
                if requestedGranularity == 'boolean':
                    break
                dataset_samples[query_response.dataset_id].update(query_response.sample_names)

        query_results = queue.Queue()
        threads = []

        for dataset_id, sample_names in dataset_samples.items():
            if (len(sample_names)) > 0:
                if requestedGranularity == 'boolean':
                    query = get_bool_query(dataset_id, sample_names)
                    thread = threading.Thread(
                        target=Biosample.get_existence_by_query,
                        kwargs={ 
                            'query': query,
                            'queue': query_results
                        }
                    )
                elif requestedGranularity == 'count':
                    query = get_count_query(dataset_id, sample_names)
                    thread = threading.Thread(
                        target=Biosample.get_count_by_query,
                        kwargs={ 
                            'query': query,
                            'queue': query_results
                        }
                    )
                elif requestedGranularity in ('record', 'aggregated'):
                    query = get_record_query(dataset_id, sample_names, skip, limit)
                    thread = threading.Thread(
                        target=Biosample.get_by_query,
                        kwargs={ 
                            'query': query,
                            'queue': query_results
                        }
                    )
                thread.start()
                threads.append(thread)

        [thread.join() for thread in threads]
        query_results = list(query_results.queue)

        query = VariantQuery.get(query_id)
        query.update(actions=[
            VariantQuery.complete.set(True), 
            VariantQuery.elapsedTime.set((get_current_time_utc() - query.startTime).total_seconds())
        ])

        if requestedGranularity == 'boolean':
            exists = any(query_results)
            response = responses.get_boolean_response(exists=exists)
            print('Returning Response: {}'.format(json.dumps(response)))
            return bundle_response(200, response, query_id)

        if requestedGranularity == 'count':
            count = sum(query_results)
            response = responses.get_counts_response(exists=count > 0, count=count)
            print('Returning Response: {}'.format(json.dumps(response)))
            return bundle_response(200, response, query_id)

        if requestedGranularity in ('record', 'aggregated'):
            biosamples = [biosample for biosamples in query_results for biosample in biosamples]

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
