import boto3
import os
import time


athena = boto3.client('athena')


def run_query(query, database, workgroup, queue=None):
    response = athena.start_query_execution(
        QueryString=query,
        # ClientRequestToken='string',
        QueryExecutionContext={
            'Database': database
        },
        WorkGroup=workgroup
    )

    retries = 0
    while True:
        exec = athena.get_query_execution(
            QueryExecutionId=response['QueryExecutionId']
        )
        status = exec['QueryExecution']['Status']['State']
        
        if status in ('QUEUED', 'RUNNING'):
            time.sleep(2)
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
                MaxResults=1000
            )
            if queue is not None:
                return queue.put(data['ResultSet']['Rows'])
            else:
                return data['ResultSet']['Rows']