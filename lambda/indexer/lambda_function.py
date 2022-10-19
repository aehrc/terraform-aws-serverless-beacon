from collections import defaultdict
import os
import boto3
import time
import threading

from generate_query_index import get_ctas_terms_index_query
from generate_query_terms import get_ctas_terms_query


athena = boto3.client('athena')
s3 = boto3.client('s3')

BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']
METADATA_BUCKET = os.environ['METADATA_BUCKET']
ATHENA_WORKGROUP = os.environ['ATHENA_WORKGROUP']
METADATA_DATABASE = os.environ['METADATA_DATABASE']
DATASETS_TABLE = os.environ['DATASETS_TABLE']
COHORTS_TABLE = os.environ['COHORTS_TABLE']
INDIVIDUALS_TABLE = os.environ['INDIVIDUALS_TABLE']
BIOSAMPLES_TABLE = os.environ['BIOSAMPLES_TABLE']
RUNS_TABLE = os.environ['RUNS_TABLE']
ANALYSES_TABLE = os.environ['ANALYSES_TABLE']
TERMS_INDEX_TABLE = os.environ['TERMS_INDEX_TABLE']
TERMS_TABLE = os.environ['TERMS_TABLE']


# def get_ontology_resources(ontologies_in_beacon=set()):
#     ontologies_url = 'http://www.ebi.ac.uk/ols/api/ontologies?page=0&size=1000'
#     response = requests.get(ontologies_url)

#     if response:
#         response_json = response.json()
#         chosen_resources = []
#         for ontology in response_json["_embedded"]["ontologies"]:
#             res_id = ontology['ontologyId']

#             if res_id.upper() not in ontologies_in_beacon:
#                 continue

#             resource = {
#                 "id": res_id,
#                 "name": ontology['config']['title'],
#                 "url": ontology['config']['fileLocation'],
#                 "version": ontology['config']['version'],
#                 "namespacePrefix": ontology['config']['preferredPrefix'],
#                 "iriPrefix": ontology['config']['baseUris'][0]
#             }

#             chosen_resources.append()
#     else:
#         raise Exception('API Error')


def update_athena_partitions(table):
    athena.start_query_execution(
        QueryString=f'MSCK REPAIR TABLE `{table}`',
        # ClientRequestToken='string',
        QueryExecutionContext={
            'Database': METADATA_DATABASE
        },
        WorkGroup=ATHENA_WORKGROUP
    )


def get_result(execution_id):
    retries = 0
    while True:
        exec = athena.get_query_execution(
            QueryExecutionId=execution_id
        )
        status = exec['QueryExecution']['Status']['State']
        
        if status in ('QUEUED', 'RUNNING'):
            sleep = min(300, 10 * (2**retries))
            print(f'Sleeping {sleep} seconds')
            time.sleep(sleep)
            retries += 1

            if retries == 6:
                print('Timed out')
                return []
            continue
        elif status in ('FAILED', 'CANCELLED'):
            print('Error: ', exec['QueryExecution']['Status'])
            raise Exception('Error: ' + str(exec['QueryExecution']['Status']))
        else:
            data = athena.get_query_results(
                QueryExecutionId=execution_id,
                # NextToken='string',
                MaxResults=1000
            )
            return data['ResultSet']['Rows']


def drop_tables(table):
    query = f'DROP TABLE IF EXISTS {table};'
    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': METADATA_DATABASE
        },
        WorkGroup=ATHENA_WORKGROUP
    )
    get_result(response['QueryExecutionId'])


def clean_files(bucket, prefix):
    has_more = True

    while has_more:
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        for object in response.get('Contents', []):
            s3.delete_object(Bucket=bucket, Key=object['Key'])
        has_more = response['IsTruncated']


def index_terms():
    clean_files(METADATA_BUCKET, 'terms_index')
    drop_tables(TERMS_INDEX_TABLE)
    
    response = athena.start_query_execution(
        QueryString=get_ctas_terms_index_query(f's3://{METADATA_BUCKET}/terms_index/'),
        QueryExecutionContext={
            'Database': METADATA_DATABASE
        },
        WorkGroup=ATHENA_WORKGROUP
    )
    get_result(response['QueryExecutionId'])


def record_terms():
    clean_files(METADATA_BUCKET, 'terms')
    drop_tables(TERMS_TABLE)
    
    response = athena.start_query_execution(
        QueryString=get_ctas_terms_query(f's3://{METADATA_BUCKET}/terms/'),
        QueryExecutionContext={
            'Database': METADATA_DATABASE
        },
        WorkGroup=ATHENA_WORKGROUP
    )
    get_result(response['QueryExecutionId'])


def lambda_handler(event, context):
    threads = []
    # TODO decide a better of partitioning or not partitioning
    # for table in (DATASETS_TABLE, COHORTS_TABLE, INDIVIDUALS_TABLE, BIOSAMPLES_TABLE, RUNS_TABLE, ANALYSES_TABLE):
    #     threads.append(threading.Thread(target=update_athena_partitions, kwargs={'table': table}))
    threads.append(threading.Thread(target=index_terms))
    threads.append(threading.Thread(target=record_terms))
    [thread.start() for thread in threads]
    [thread.join() for thread in threads]

    print('Success')


if __name__ == '__main__':
    # lambda_handler({}, {})
    # import requests
    # import urllib.parse
    # # ontology = 'doid'
    # # iri = "http://purl.obolibrary.org/obo/DOID_0110749"
    # # iri_double_encoded = urllib.parse.quote_plus(urllib.parse.quote_plus(iri))
    # # url = f'https://www.ebi.ac.uk/ols/api/ontologies/{ontology}/terms/{iri_double_encoded}/hierarchicalAncestors'
    # # response = requests.get(url)

    # # if response:
    # #     pass
    # # else:
    # #     raise Exception('API Error')


    # ontologies_url = 'http://www.ebi.ac.uk/ols/api/ontologies?page=0&size=5'
    # response = requests.get(ontologies_url)

    # if response:
    #     response_json = response.json()
    #     for ontology in response_json["_embedded"]["ontologies"]:
    #         resource = {
    #             "id": ontology['ontologyId'],
    #             "name": ontology['config']['title'],
    #             "url": ontology['config']['fileLocation'],
    #             "version": ontology['config']['version'],
    #             "namespacePrefix": ontology['config']['preferredPrefix'],
    #             "iriPrefix": ontology['config']['baseUris'][0]
    #         }
    #         # print(ontology['ontologyId'])
    #         # print(ontology['config']['title'])
    #         # print(ontology['config']['fileLocation'])
    #         # print(ontology['config']['version'])
    #         # print(ontology['config']['preferredPrefix'])
    #         # print(ontology['config']['baseUris'][0])
    #         print(resource)
    # else:
    #     raise Exception('API Error')
    pass
 