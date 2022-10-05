from collections import defaultdict
import json
import queue
import threading
import os
import base64
import jsons


from apiutils.api_response import bundle_response, bad_request
from variantutils.search_variants import perform_variant_search
import apiutils.responses as responses
from athena.biosample import Biosample
from dynamodb.onto_index import OntoData
from athena.dataset import get_datasets


BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
INDIVIDUALS_TABLE = os.environ['INDIVIDUALS_TABLE']
BIOSAMPLES_TABLE = os.environ['BIOSAMPLES_TABLE']
ANALYSES_TABLE = os.environ['ANALYSES_TABLE']


def get_count_query(dataset_id, sample_names, conditions=[]):
    query = f'''
    SELECT COUNT(*)
    FROM "{{database}}"."{ANALYSES_TABLE}" JOIN "{{database}}"."{BIOSAMPLES_TABLE}" 
    ON 
        "{{database}}"."{ANALYSES_TABLE}".biosampleid
        =
        "{{database}}"."{BIOSAMPLES_TABLE}".id
    WHERE 
        "{{database}}"."{ANALYSES_TABLE}"._datasetid='{dataset_id}'
        AND 
        "{{database}}"."{BIOSAMPLES_TABLE}"._datasetid='{dataset_id}'
        AND
            "{{database}}"."{ANALYSES_TABLE}".vcfsampleid"
        IN ({','.join([f"'{sn}'" for sn in sample_names])})
        {('AND ' if len(conditions) > 0 else '') + ' AND '.join(conditions)}
    '''
    return query


def get_bool_query(dataset_id, sample_names, conditions=[]):
    query = f'''
    SELECT 1
    FROM "{{database}}"."{ANALYSES_TABLE}" JOIN "{{database}}"."{BIOSAMPLES_TABLE}" 
    ON 
        "{{database}}"."{ANALYSES_TABLE}".id
        =
        "{{database}}"."{BIOSAMPLES_TABLE}".individualid
    WHERE 
        "{{database}}"."{ANALYSES_TABLE}"._datasetid='{dataset_id}'
        AND 
        "{{database}}"."{BIOSAMPLES_TABLE}"._datasetid='{dataset_id}'
        AND
            "{{database}}"."{ANALYSES_TABLE}".vcfsampleid
        IN ({','.join([f"'{sn}'" for sn in sample_names])})
        {('AND ' if len(conditions) > 0 else '') + ' AND '.join(conditions)}
    LIMIT 1
    '''
    return query


# TODO break into many queries (ATHENA SQL LIMIT)
# https://docs.aws.amazon.com/athena/latest/ug/service-limits.html
def get_record_query(dataset_id, sample_names, skip, limit, conditions=[]):
    query = f'''
    SELECT "{{database}}"."{BIOSAMPLES_TABLE}".* 
    FROM "{{database}}"."{ANALYSES_TABLE}" JOIN "{{database}}"."{BIOSAMPLES_TABLE}" 
    ON 
        "{{database}}"."{ANALYSES_TABLE}".id
        =
        "{{database}}"."{BIOSAMPLES_TABLE}".individualid
    WHERE 
        "{{database}}"."{ANALYSES_TABLE}"._datasetid='{dataset_id}'
        AND 
        "{{database}}"."{BIOSAMPLES_TABLE}"._datasetid='{dataset_id}'
        AND
            "{{database}}"."{ANALYSES_TABLE}"._vcfsampleid 
        IN ({','.join([f"'{sn}'" for sn in sample_names])})
        {('AND ' if len(conditions) > 0 else '') + ' AND '.join(conditions)}
    ORDER BY "id", "individualid"
    OFFSET {skip}
    LIMIT {limit};
    '''
    return query


def route(event):
    if event['httpMethod'] == 'GET':
        params = event.get('queryStringParameters', dict()) or dict()
        print(f"Query params {params}")
        apiVersion = params.get("apiVersion", BEACON_API_VERSION)
        requestedSchemas = params.get("requestedSchemas", [])
        requestedGranularity = params.get("requestedGranularity", "boolean")
        # skip = params.get("skip", 0)
        # limit = params.get("limit", 100)
        currentPage = params.get("currentPage", None)
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
        # skip = pagination.get("skip", 0)
        # limit = pagination.get("limit", 100)
        currentPage = pagination.get("currentPage", None)
        previousPage = pagination.get("previousPage", None)
        nextPage = pagination.get("nextPage", None)
        filters = query.get("filters", [])
        requestParameters = query.get("requestParameters", dict())

    # pagination format = variant skip, limit, individuals skip, limit
    if currentPage is None:
        currentPage = f'0:10,0:10'
        skip1, limit1 = 0, 10
        skip2, limit2 = 0, 10
    else:
        pag1, pag2 = currentPage.split(',')
        skip1, limit1 = list(map(int, pag1.split(':')))
        skip2, limit2 = list(map(int, pag2.split(':')))

    variant_id = event["pathParameters"].get("id", None)
    if variant_id is None:
        return bad_request(errorMessage="Request missing variant ID")
    
    dataset_hash = base64.b64decode(variant_id.encode()).decode()
    assemblyId, referenceName, pos, referenceBases, alternateBases = dataset_hash.split('\t')
    pos = int(pos) - 1
    start = [pos, pos + len(alternateBases)]
    end = [pos, pos + len(alternateBases)]
    datasets = get_datasets(assemblyId, skip=skip1, limit=limit1)
    includeResultsetResponses = 'ALL'


    # by default the scope of terms is assumed to be biosamples
    terms_found = True
    biosamples_term_columns = []
    individuals_term_columns = []

    if len(filters) > 0:
        for fil in filters:
            if fil.get('scope', 'biosamples') == 'biosamples':
                terms_found = False
                for item in OntoData.tableTermsIndex.query(hash_key=f'{BIOSAMPLES_TABLE}\t{fil["id"]}'):
                    biosamples_term_columns.append((item.term, item.columnName))
                    terms_found = True
    
            # TODO
            # if fil.get('scope') == 'individuals':
            #     terms_found = False
            #     for item in OntoData.tableTermsIndex.query(hash_key=f'{INDIVIDUALS_TABLE}\t{fil["id"]}'):
            #         individuals_term_columns.append((item.term, item.columnName))
            #         terms_found = True
   
    sql_conditions = []

    for term, col in biosamples_term_columns:
        cond = f'''
            JSON_EXTRACT_SCALAR("{BIOSAMPLES_TABLE}"."{col}", '$.id')='{term}' 
        '''
        sql_conditions.append(cond)

    # TODO
    # for term, col in individuals_term_columns:
    #     cond = f'''
    #         JSON_EXTRACT_SCALAR("{INDIVIDUALS_TABLE}"."{col}", '$.id')='{term}' 
    #     '''
    #     sql_conditions.append(cond)
    
    dataset_samples = defaultdict(set)

    if not terms_found:
        response = responses.get_boolean_response(exists=False)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    samples_found, query_responses = perform_variant_search(
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
        requestedGranularity=requestedGranularity,
        includeResultsetResponses=includeResultsetResponses
    )

    # immediately return
    if not samples_found and requestedGranularity == 'boolean':
        response = responses.get_boolean_response(exists=False)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    for query_response in query_responses:
        if query_response.exists:
            dataset_samples[query_response.dataset_id].update(query_response.sample_names)

    query_results = queue.Queue()
    threads = []

    for dataset_id, sample_names in dataset_samples.items():
        if (len(sample_names)) > 0:
            if requestedGranularity == 'boolean':
                query = get_bool_query(dataset_id, sample_names, sql_conditions)
                thread = threading.Thread(
                    target=Biosample.get_existence_by_query,
                    kwargs={ 
                        'query': query,
                        'queue': query_results
                    }
                )
            elif requestedGranularity == 'count':
                query = get_count_query(dataset_id, sample_names, sql_conditions)
                thread = threading.Thread(
                    target=Biosample.get_count_by_query,
                    kwargs={ 
                        'query': query,
                        'queue': query_results
                    }
                )
            elif requestedGranularity in ('record', 'aggregated'):
                query = get_record_query(dataset_id, sample_names, skip2, limit2, sql_conditions)
                thread = threading.Thread(
                    target=Biosample.get_by_query,
                    kwargs={ 
                        'query': query,
                        'queue': query_results
                    }
                )
            else:
                return bad_request(errorMessage='Invalid granularity')
            thread.start()
            threads.append(thread)

    [thread.join() for thread in threads]
    query_results = list(query_results.queue)

    if requestedGranularity == 'boolean':
        exists = any(query_results)
        response = responses.get_boolean_response(exists=exists)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if requestedGranularity == 'count':
        count = sum(query_results)
        response = responses.get_counts_response(exists=count > 0, count=count)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if requestedGranularity in ('record', 'aggregated'):
        biosamples = [biosample for biosamples in query_results for biosample in biosamples]

        response = responses.get_result_sets_response(
            setType='biosample', 
            info={
                'paginationNote': 'Paginate using skip1:limit1,skip2:limit2 paging convetion, skip1 and limit1 are applied on datasets while skip2 and limit2 are applied on individuals represented by each dataset'
            },
            reqPagination=responses.get_cursor_object(currentPage=currentPage, nextPage='', previousPage=''),
            exists=len(biosamples) > 0,
            total=len(biosamples),
            results=jsons.dump(biosamples, strip_privates=True)
        )
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)


if __name__ == '__main__':
    pass
