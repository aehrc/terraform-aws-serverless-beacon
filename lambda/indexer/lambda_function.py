from collections import defaultdict
import os
import boto3
import time
import threading
import queue
import pickle

from smart_open import open as sopen


athena = boto3.client('athena')

BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']
ATHENA_WORKGROUP = os.environ['ATHENA_WORKGROUP']
METADATA_DATABASE = os.environ['METADATA_DATABASE']
INDIVIDUALS_TABLE = os.environ['INDIVIDUALS_TABLE']
BIOSAMPLES_TABLE = os.environ['BIOSAMPLES_TABLE']
METADATA_BUCKET = os.environ['METADATA_BUCKET']
ONTO_INDEX_QUERY = open('helper_queries.sql').read().strip()

def update_athena_partitions():
    athena.start_query_execution(
        QueryString=f'MSCK REPAIR TABLE `{INDIVIDUALS_TABLE}`',
        # ClientRequestToken='string',
        QueryExecutionContext={
            'Database': METADATA_DATABASE
        },
        WorkGroup=ATHENA_WORKGROUP
    )


def onto_index():
    response = athena.start_query_execution(
        QueryString=ONTO_INDEX_QUERY,
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
            sleep = 10 * (2**retries)
            print(f'Sleeping {sleep} seconds')
            time.sleep(sleep)
            retries += 1

            if retries == 4:
                print('Timed out')
                return []
            continue
        elif status in ('FAILED', 'CANCELLED'):
            print('Error: ', exec['QueryExecution']['Status'])
            return
        else:
            data = athena.get_query_results(
                QueryExecutionId=response['QueryExecutionId'],
                # NextToken='string',
                MaxResults=1000
            )
            data = data['ResultSet']['Rows'][1:]
            
            onto_tables = defaultdict(list)
            filtering_terms = []

            for row in data:
                onto_tables[row['Data'][0]['VarCharValue']].append(
                    (
                        row['Data'][3]['VarCharValue'], 
                        row['Data'][4]['VarCharValue']
                    )
                )
                filtering_terms.append({
                    "id": row['Data'][0]['VarCharValue'],
                    # only field that can be empty
                    "label": row['Data'][1].get('VarCharValue', ''),
                    "type": row['Data'][2]['VarCharValue']
                })
            with sopen(f's3://{METADATA_BUCKET}/indexes/onto_index.pkl', 'wb') as fo:
                pickle.dump(dict(onto_tables), fo)
            with sopen(f's3://{METADATA_BUCKET}/indexes/filtering_terms.pkl', 'wb') as fo:
                pickle.dump(filtering_terms, fo)
            return


def lambda_handler(event, context):
    t_1 = threading.Thread(target=update_athena_partitions)
    t_2 = threading.Thread(target=onto_index)
    t_1.start()
    t_2.start()

    t_1.join()
    t_2.join()
    print('Success')


if __name__ == '__main__':
    lambda_handler({}, {})
