from collections import defaultdict
import os
import boto3
import time
import threading

from smart_open import open as sopen
import pyorc

from dynamodb.onto_index import OntoData


athena = boto3.client('athena')

BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']
ATHENA_WORKGROUP = os.environ['ATHENA_WORKGROUP']
METADATA_DATABASE = os.environ['METADATA_DATABASE']
INDIVIDUALS_TABLE = os.environ['INDIVIDUALS_TABLE']
BIOSAMPLES_TABLE = os.environ['BIOSAMPLES_TABLE']
METADATA_BUCKET = os.environ['METADATA_BUCKET']
ONTO_INDEX_QUERY = open('helper_queries.sql').read().strip()


def update_athena_partitions(table):
    athena.start_query_execution(
        QueryString=f'MSCK REPAIR TABLE `{table}`',
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

            with sopen(f's3://{METADATA_BUCKET}/terms/terms.orc', 'wb') as s3file:
                header = 'struct<term:string,label:string,type:string,table:string>'
                with pyorc.Writer(s3file, 
                    header, 
                    compression=pyorc.CompressionKind.SNAPPY, 
                    compression_strategy=pyorc.CompressionStrategy.COMPRESSION) as writer:
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
                        entry = OntoData.make_index_entry(
                            term=row['Data'][0]['VarCharValue'],
                            tableName=row['Data'][3]['VarCharValue'],
                            columnName=row['Data'][4]['VarCharValue'],
                            type=row['Data'][2]['VarCharValue'],
                            label= row['Data'][1].get('VarCharValue', '')
                        )
                        writer.write((entry.term, entry.label, entry.type, entry.tableName))
                        entry.save()
            return


def lambda_handler(event, context):
    threads = []
    for table in (INDIVIDUALS_TABLE, BIOSAMPLES_TABLE):
        threads.append(threading.Thread(target=update_athena_partitions, kwargs={'table': table}))
    threads.append(threading.Thread(target=onto_index))
    [thread.start() for thread in threads]
    [thread.join() for thread in threads]

    print('Success')


if __name__ == '__main__':
    lambda_handler({}, {})
