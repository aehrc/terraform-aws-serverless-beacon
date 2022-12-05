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

from generate_query_index import QUERY as INDEX_QUERY
from generate_query_terms import QUERY as TERMS_QUERY
from generate_query_relations import QUERY as RELATIONS_QUERY
from dynamodb.ontologies import Ontology, Descendants, Anscestors
from dynamodb.onto_index import OntoData


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
TERMS_CACHE_TABLE = os.environ['TERMS_CACHE_TABLE']
TERMS_TABLE = os.environ['TERMS_TABLE']
RELATIONS_TABLE = os.environ['RELATIONS_TABLE']

ENSEMBL_OLS = 'https://www.ebi.ac.uk/ols/api/ontologies'
ONTOSERVER = 'https://r4.ontoserver.csiro.au/fhir/ValueSet/$expand'
ONTO_TERMS_QUERY = f''' SELECT term,tablename,colname,type,label FROM "{TERMS_TABLE}" '''
INDEX_QUERY = INDEX_QUERY.format(table=TERMS_CACHE_TABLE, uri=f's3://{METADATA_BUCKET}/terms-index/')
TERMS_QUERY = TERMS_QUERY.format(table=TERMS_CACHE_TABLE, uri=f's3://{METADATA_BUCKET}/terms/')
RELATIONS_QUERY = RELATIONS_QUERY.format(
    uri=f's3://{METADATA_BUCKET}/relations/',
    individuals_table=INDIVIDUALS_TABLE,
    biosamples_table=BIOSAMPLES_TABLE,
    runs_table=RUNS_TABLE,
    analyses_table=ANALYSES_TABLE
)


# in future, there could be an issue when descendants entries exceed 400KB
# which means we would have roughtly 20480, 20 byte entries (unlikely?)
# this would also mean, our SQL queries would reach the 256KB limit
# we should be able to easily spread terms across multiple dynamodb
# entries and have multiple queries (as recommended by AWS)
def index_terms_tree():
    # subroutine for ensemble
    def threaded_request_ensemble(term, url, queue):
        response = requests.get(url)
        if response:
            response_json = response.json()
            anscestors = set()
            for response_term in response_json['_embedded']['terms']:
                obo_id = response_term['obo_id']
                if obo_id:
                    anscestors.add(obo_id)
            if len(anscestors) > 0:
                queue.put((term, anscestors))


    # subroutine for ontoserver
    def threaded_request_ontoserver(term, url, queue=None):
        snomed = 'SNOMED' in term.upper()
        retries = 1
        response = None
        while (not response or response.status_code != 200) and retries < 10:
            retries += 1
            response = requests.post(url, json={
                "resourceType": "Parameters",
                "parameter": [{"name": "valueSet", "resource": {"resourceType": "ValueSet", "compose": {"include": [{"system": data['baseUri'], "filter": [{"property": "concept", "op": "generalizes", "value": f"{term.replace('SNOMED:', '')}"}]}]}}}]
            })
            if response.status_code == 200:
                response_json = response.json()
                anscestors = set()
                for response_term in response_json['expansion']['contains']:
                    anscestors.add(
                        'SNOMED:' + response_term['code'] if snomed else response_term['code'])
                if len(anscestors) > 0:
                    queue.put((term, anscestors))
            else:
                time.sleep(1)
        if response.status_code != 200:
            print(f'Fetching SNOMED failed for term = {term}')

    query = f'SELECT DISTINCT term FROM "{TERMS_TABLE}"'

    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': METADATA_DATABASE
        },
        WorkGroup=ATHENA_WORKGROUP
    )

    execution_id = response['QueryExecutionId']
    get_result(execution_id, sleep=2)

    ontologies = set()
    ontology_clusters = defaultdict(set)
    term_anscestors = defaultdict(set)
    threads = []
    response_queue = Queue()

    with sopen(f's3://{METADATA_BUCKET}/query-results/{execution_id}.csv') as s3f:
        for n, line in enumerate(s3f):
            if n == 0:
                continue
            term = line.strip().strip('"')

            # beacon API does not allow non CURIE formatted terms
            # however, SNOMED appears are non-CURIE prefixed terms
            # following is to support that, however API will not ingest
            # always submit in form SNOMED:123212
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
            if ontology == 'SNOMED':
                # use ontoserver
                entry = Ontology(ontology.upper())
                entry.data = json.dumps({
                    "id": 'SNOMED',
                    "baseUri": "http://snomed.info/sct"
                })
                entry.save()
                details = entry
            else:
                # use ENSEMBL
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
                terms = ontology_clusters[ontology]

                for term in terms:
                    # fetch only anscestors that aren't fetched yet
                    try:
                        data = Anscestors.get(term)
                    except Anscestors.DoesNotExist:
                        data = json.loads(details.data)
                        thread = threading.Thread(target=threaded_request_ontoserver, args=(term, ONTOSERVER, response_queue))
                        thread.start()
                        threads.append(thread)
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
                        thread = threading.Thread(target=threaded_request_ensemble, args=(term, url, response_queue))
                        thread.start()
                        threads.append(thread)

    [thread.join() for thread in threads]

    for term, ancestors in list(response_queue.queue):
        term_anscestors[term].update(ancestors)
        term_anscestors[term].add(term)

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


def get_result(execution_id, sleep=10):
    retries = 0
    while True:
        exec = athena.get_query_execution(
            QueryExecutionId=execution_id
        )
        status = exec['QueryExecution']['Status']['State']

        if status in ('QUEUED', 'RUNNING'):
            print(f'Sleeping {sleep} seconds')
            time.sleep(sleep)
            retries += 1

            if retries == 60:
                print('Timed out')
                return []
            continue
        elif status in ('FAILED', 'CANCELLED'):
            print('Error: ', exec['QueryExecution']['Status'])
            raise Exception('Error: ' + str(exec['QueryExecution']['Status']))
        else:
            data = athena.get_query_results(
                QueryExecutionId=execution_id,
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
    get_result(response['QueryExecutionId'], sleep=1)


def clean_files(bucket, prefix):
    has_more = True
    while has_more:
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        files_to_delete = []
        for object in response.get('Contents', []):
            files_to_delete.append({"Key": object["Key"]})
        if files_to_delete:
            s3.delete_objects(
                Bucket=bucket,
                Delete={"Objects": files_to_delete})
        has_more = response['IsTruncated']
    time.sleep(1)


def index_terms():
    clean_files(METADATA_BUCKET, 'terms-index/')
    drop_tables(TERMS_INDEX_TABLE)

    response = athena.start_query_execution(
        QueryString=INDEX_QUERY,
        QueryExecutionContext={
            'Database': METADATA_DATABASE
        },
        WorkGroup=ATHENA_WORKGROUP
    )
    get_result(response['QueryExecutionId'])


def record_terms():
    clean_files(METADATA_BUCKET, 'terms/')
    drop_tables(TERMS_TABLE)

    response = athena.start_query_execution(
        QueryString=TERMS_QUERY,
        QueryExecutionContext={
            'Database': METADATA_DATABASE
        },
        WorkGroup=ATHENA_WORKGROUP
    )
    get_result(response['QueryExecutionId'])


def record_relations():
    clean_files(METADATA_BUCKET, 'relations/')
    drop_tables(RELATIONS_TABLE)

    response = athena.start_query_execution(
        QueryString=RELATIONS_QUERY,
        QueryExecutionContext={
            'Database': METADATA_DATABASE
        },
        WorkGroup=ATHENA_WORKGROUP
    )
    get_result(response['QueryExecutionId'])


# TODO re-evaluate the following function remove or useful?
def onto_index():
    response = athena.start_query_execution(
        QueryString=ONTO_TERMS_QUERY,
        QueryExecutionContext={
            'Database': METADATA_DATABASE
        },
        WorkGroup=ATHENA_WORKGROUP
    )
    execution_id = response['QueryExecutionId']
    get_result(execution_id)
    
    with sopen(f's3://{METADATA_BUCKET}/query-results/{execution_id}.csv') as s3f:
        for n, line in enumerate(s3f):
            if n == 0:
                continue
            term, tablename, colname, type, label = [item.strip('"') for item in line.strip().split(',')]
            entry = OntoData.make_index_entry(
                term=term,
                tableName=tablename,
                columnName=colname,
                type=type,
                label= label
            )
            entry.save()
    return


def lambda_handler(event, context):
    # TODO decide a better way of partitioning or not partitioning
    # for table in (DATASETS_TABLE, COHORTS_TABLE, INDIVIDUALS_TABLE, BIOSAMPLES_TABLE, RUNS_TABLE, ANALYSES_TABLE):
    #     threads.append(threading.Thread(target=update_athena_partitions, kwargs={'table': table}))
    # this is the longest process
    index_thread = threading.Thread(target=index_terms)
    index_thread.start()
    
    relations_thread = threading.Thread(target=record_relations)
    relations_thread.start()

    # terms are neded for the tree index
    terms_thread = threading.Thread(target=record_terms)
    terms_thread.start()
    terms_thread.join()
    index_terms_tree()

    # join last running threads
    index_thread.join()
    relations_thread.join()
    print('Success')


if __name__ == '__main__':
    lambda_handler({}, {})
    pass
