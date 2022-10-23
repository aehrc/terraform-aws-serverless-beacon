from collections import defaultdict
import os
from queue import Queue
import boto3
import time
import threading
import re
import requests
import json
import urllib
import threading

from smart_open import open as sopen

from generate_query_index import get_ctas_terms_index_query
from generate_query_terms import get_ctas_terms_query
from dynamodb.ontologies import Ontology, Descendants, Anscestors


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

ENSEMBL_OLS = 'https://www.ebi.ac.uk/ols/api/ontologies'


# in future, there could be an issue when descendants entries exceed 400KB
# which means we would have roughtly 20480, 20 byte entries (unlikely?)
# this would also mean, our SQL queries would reach the 256KB limit
# we should be able to easily spread terms across multiple dynamodb 
# entries and have multiple queries (as recommended by AWS)
def index_terms_tree():
    def threaded_request(term, url, queue):
        response = requests.get(url)
        queue.put((term, response))

    query = f'SELECT DISTINCT term FROM "{TERMS_TABLE}"'
    
    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': METADATA_DATABASE
        },
        WorkGroup=ATHENA_WORKGROUP
    )

    execution_id = response['QueryExecutionId']
    get_result(execution_id)

    ontologies = set()
    ontology_clusters = defaultdict(set)
    term_anscestors = defaultdict(set)
    threads = []
    response_queue = Queue()

    with sopen(f's3://{METADATA_BUCKET}/query-results/{execution_id}.csv') as s3f:
        for n, line in enumerate(s3f):
            if n == 0: continue
            term = line.strip().strip('"')

            if re.match(r'(?i)(^SNOMED)|([0-9]+)', term):
                ontology = 'SNOMED'
                ontologies.add(ontology)
                ontology_clusters[ontology].add(term)
            else:
                ontology = term.split(':')[0]
                ontologies.add(ontology)
                ontology_clusters[ontology].add(term)
    
    for ontology in ontologies:
        try:
            details = Ontology.get(ontology)
        except Ontology.DoesNotExist:
            response = requests.get(f'{ENSEMBL_OLS}/{ontology}')
            if response:
                response_json = response.json()
                entry = Ontology(ontology.upper())
                entry.data = json.dumps({
                    "id": response_json["ontologyId"].upper(),
                    "baseUri": response_json["config"]["baseUris"][0]
                })
                entry.save()
                details = entry
            else:
                details = None
        
        if details:
            if ontology == 'SNOMED':
                pass
            else:
                terms = ontology_clusters[ontology]
                
                for term in terms:
                    # fetch only anscestors that aren't fetched yet
                    try:
                        data = Anscestors.get(term)
                    except Anscestors.DoesNotExist:
                        data = json.loads(details.data)
                        iri = data['baseUri'] + term.split(':')[1]
                        iri_double_encoded = urllib.parse.quote_plus(urllib.parse.quote_plus(iri))
                        url = f'{ENSEMBL_OLS}/{ontology}/terms/{iri_double_encoded}/hierarchicalAncestors'

                        thread = threading.Thread(target=threaded_request, args=(term, url, response_queue))
                        thread.start()
                        threads.append(thread)

    [thread.join() for thread in threads]

    for term, response in list(response_queue.queue):
        if response:
            response_json = response.json()
            for response_term in response_json['_embedded']['terms']:
                obo_id = response_term['obo_id']
                if obo_id:
                    term_anscestors[term].add(obo_id)

    term_descendants = defaultdict(set)

    with Anscestors.batch_write() as batch:
        for term, anscestors in term_anscestors.items():
            item = Anscestors(term)
            item.anscestors = anscestors
            batch.save(item)

            for anscestor in anscestors:
                term_descendants[anscestor].add(term)

    with Descendants.batch_write() as batch:
        for term, descendants in term_descendants.items():
            # if descendants are recorded, just update, else make record
            try:
                item = Descendants.get(term)
                item.update(actions=[
                    Descendants.descendants.add(descendants)
                ])
            except Descendants.DoesNotExist:
                item = Descendants(term)
                item.descendants = descendants
                batch.save(item)


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
    threads.append(threading.Thread(target=index_terms_tree))
    [thread.start() for thread in threads]
    [thread.join() for thread in threads]

    print('Success')


if __name__ == '__main__':
    pass
 