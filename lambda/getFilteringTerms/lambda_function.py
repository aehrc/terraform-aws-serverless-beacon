import json
import os
from unittest import result
import boto3
import time
import threading
import queue

from apiutils.api_response import bundle_response


athena = boto3.client('athena')

BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']
ATHENA_WORKGROUP = os.environ['ATHENA_WORKGROUP']
METADATA_DATABASE = os.environ['METADATA_DATABASE']
INDIVIDUALS_TABLE = os.environ['INDIVIDUALS_TABLE']
BIOSAMPLES_TABLE = os.environ['BIOSAMPLES_TABLE']
# contains the aggregate query for all the ontology terms
QUERIES = [
    f'''
    SELECT distinct CAST(term AS varchar) AS term, CAST(label AS varchar), CAST(type AS varchar) 
    FROM (
        SELECT distinct json_extract(biosamplestatus, '$.id') AS term, json_extract(biosamplestatus, '$.label') AS label, 'string' AS type 
        FROM "{METADATA_DATABASE}"."{BIOSAMPLES_TABLE}"
        WHERE json_extract(biosamplestatus, '$.id') 
        IS NOT NULL
            UNION
        SELECT distinct json_extract(histologicaldiagnosis, '$.id') AS term, json_extract(histologicaldiagnosis, '$.label') AS label, 'string' AS type 
        FROM "{METADATA_DATABASE}"."{BIOSAMPLES_TABLE}"
        WHERE json_extract(histologicaldiagnosis, '$.id') 
        IS NOT NULL
            UNION
        SELECT distinct json_extract(obtentionprocedure, '$.code.id') AS term, json_extract(obtentionprocedure, '$.code.label') AS label, 'string' AS type 
        FROM "{METADATA_DATABASE}"."{BIOSAMPLES_TABLE}"
        WHERE json_extract(obtentionprocedure, '$.code.id') 
        IS NOT NULL
            UNION
        SELECT distinct json_extract(pathologicalstage, '$.id') AS term, json_extract(pathologicalstage, '$.label') AS label, 'string' AS type 
        FROM "{METADATA_DATABASE}"."{BIOSAMPLES_TABLE}"
        WHERE json_extract(pathologicalstage, '$.id') 
        IS NOT NULL
            UNION
        SELECT distinct json_extract(pathologicaltnmfinding, '$.id') AS term, json_extract(pathologicaltnmfinding, '$.label') AS label, 'string' AS type 
        FROM "{METADATA_DATABASE}"."{BIOSAMPLES_TABLE}"
        WHERE json_extract(pathologicaltnmfinding, '$.id') 
        IS NOT NULL
            UNION
        SELECT distinct json_extract(sampleorigindetail, '$.id') AS term, json_extract(sampleorigindetail, '$.label') AS label, 'string' AS type 
        FROM "{METADATA_DATABASE}"."{BIOSAMPLES_TABLE}"
        WHERE json_extract(sampleorigindetail, '$.id') 
        IS NOT NULL
            UNION
        SELECT distinct json_extract(sampleorigintype, '$.id') AS term, json_extract(sampleorigintype, '$.label') AS label, 'string' AS type 
        FROM "{METADATA_DATABASE}"."{BIOSAMPLES_TABLE}"
        WHERE json_extract(sampleorigintype, '$.id') 
        IS NOT NULL
            UNION
        SELECT distinct json_extract(sampleprocessing, '$.id') AS term, json_extract(sampleprocessing, '$.label') AS label, 'string' AS type 
        FROM "{METADATA_DATABASE}"."{BIOSAMPLES_TABLE}"
        WHERE json_extract(sampleprocessing, '$.id') 
        IS NOT NULL
            UNION
        SELECT distinct json_extract(tumorprogression, '$.id') AS term, json_extract(tumorprogression, '$.label') AS label, 'string' AS type 
        FROM "{METADATA_DATABASE}"."{BIOSAMPLES_TABLE}"
        WHERE json_extract(tumorprogression, '$.id') 
        IS NOT NULL
    ) 
    ORDER BY term 
    ASC;
    ''',
    f'''
    SELECT distinct CAST(term AS varchar) AS term, CAST(label AS varchar), CAST(type AS varchar) FROM (
        SELECT distinct json_extract(ethnicity, '$.id') AS term, json_extract(ethnicity, '$.label') AS label, 'string' AS type 
        FROM "{METADATA_DATABASE}"."{INDIVIDUALS_TABLE}"
        WHERE json_extract(ethnicity, '$.id') 
        IS NOT NULL
            UNION
        SELECT distinct json_extract(geographicorigin, '$.id') AS term, json_extract(geographicorigin, '$.label') AS label, 'string' AS type 
        FROM "{METADATA_DATABASE}"."{INDIVIDUALS_TABLE}"
        WHERE json_extract(geographicorigin, '$.id') 
        IS NOT NULL
            UNION
        SELECT distinct json_extract(sex, '$.id') AS term, json_extract(sex, '$.label') AS label, 'string' AS type 
        FROM "{METADATA_DATABASE}"."{INDIVIDUALS_TABLE}"
        WHERE json_extract(sex, '$.id') 
        IS NOT NULL
    ) 
    ORDER BY term 
    ASC;
    '''
]


def fetch_athena_data(query, results):
    response = athena.start_query_execution(
        QueryString=query,
        # ClientRequestToken='string',
        QueryExecutionContext={
            'Database': METADATA_DATABASE
        },
        WorkGroup=ATHENA_WORKGROUP
    )

    retries = 0
    while True:
        exec = athena.get_query_execution(
            QueryExecutionId=response['QueryExecutionId']
        )
        status = exec['QueryExecution']['Status']['State']
        
        if status in ('QUEUED', 'RUNNING'):
            time.sleep(1 * (2**retries))
            retries += 1

            if retries == 4:
                print('Timed out')
                return []
            continue
        elif status in ('FAILED', 'CANCELLED'):
            print('Error: ', exec['QueryExecution']['Status'])
            return []
        else:
            data = athena.get_query_results(
                QueryExecutionId=response['QueryExecutionId'],
                # NextToken='string',
                MaxResults=1000
            )
            filteringTerms = []
            for row in data['ResultSet']['Rows'][1:]:
                term, label, typ = row['Data']
                term, label, typ = term['VarCharValue'], label['VarCharValue'], typ['VarCharValue']
                filteringTerms.append({
                    "id": term,
                    "label": label,
                    "type": typ
                })
            results.put(filteringTerms)
            return


def get_entry_types(terms):
    response =     {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "info": {},
        "meta": {
            "apiVersion": BEACON_API_VERSION,
            "beaconId": BEACON_ID,
            "returnedSchemas": []
        },
        "response": {
            "filteringTerms": terms,
            "resources": [
                {
                    "id": "NA",
                    "iriPrefix": "NA",
                    "name": "NA",
                    "namespacePrefix": "NA",
                    "url": "NA",
                    "version": "TBD"
                }
            ]
        }
    }

    return bundle_response(200, response)


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    threads = []
    results = queue.Queue()
    
    for query in QUERIES:
        thread = threading.Thread(
                target=fetch_athena_data,
                kwargs={ 'query': query , 'results': results }
            )
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()

    response = get_entry_types(
        sorted(
            [term for terms in list(results.queue) for term in terms],
            key=lambda term: term['id']
        )
    )
    print('Returning Response: {}'.format(json.dumps(response)))
    return response


if __name__ == '__main__':
    lambda_handler({}, {})
