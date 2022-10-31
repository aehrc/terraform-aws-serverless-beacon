import boto3
import os
import time


METADATA_BUCKET = os.environ['METADATA_BUCKET']
ATHENA_WORKGROUP = os.environ['ATHENA_WORKGROUP']
METADATA_DATABASE = os.environ['METADATA_DATABASE']

athena = boto3.client('athena')

# Perform database level operations based on the queries


class AthenaModel:
    '''
    This is a higher level abstraction class
    user is only required to write queries in the following form
    
    SELECT * FROM "{{database}}"."{{table}}" WHERE <CONDITIONS>;

    table name is fetched from the child class, database is injected
    in this class. Helps write cleaner code without so many constants 
    repeated everywhere.
    '''
    @classmethod
    def get_by_query(cls, query, queue=None):
        query = query.format(database=METADATA_DATABASE, table=cls._table_name)
        result = run_custom_query(query, METADATA_DATABASE, ATHENA_WORKGROUP, queue=None)

        if not len(result) > 0:
            return []
        elif queue is None:
            return cls.parse_array(result)
        else:
            queue.put(cls.parse_array(result))

    
    @classmethod
    def get_by_query_v2(cls, query, queue=None):
        query = query.format(database=METADATA_DATABASE, table=cls._table_name)
        result = run_custom_query(query, METADATA_DATABASE, ATHENA_WORKGROUP, queue=None, return_id=True)

        if not len(result) > 0:
            return []
        elif queue is None:
            return cls.parse_array_v2(result)
        else:
            queue.put(cls.parse_array_v2(result))

    
    @classmethod
    def get_existence_by_query(cls, query, queue=None):
        query = query.format(database=METADATA_DATABASE, table=cls._table_name)
        result = run_custom_query(query, METADATA_DATABASE, ATHENA_WORKGROUP, queue=None)

        if not len(result) > 0:
            return []
        elif queue is None:
            return len(result) > 1
        else:
            queue.put(len(result) > 1)


    @classmethod
    def get_count_by_query(cls, query, queue=None):
        query = query.format(database=METADATA_DATABASE, table=cls._table_name)
        result = run_custom_query(query, METADATA_DATABASE, ATHENA_WORKGROUP, queue=None)

        if not len(result) > 0:
            return []
        elif queue is None:
            return int(result[1]['Data'][0]['VarCharValue'])
        else:
            queue.put(int(result[1]['Data'][0]['VarCharValue']))


def run_custom_query(query, database=METADATA_DATABASE, workgroup=ATHENA_WORKGROUP, queue=None, return_id=False):
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
            time.sleep(0.5)
            retries += 1

            if retries == 60:
                print('Timed out')
                return []
            continue
        elif status in ('FAILED', 'CANCELLED'):
            print('Error: ', exec['QueryExecution']['Status'])
            return []
        else:
            if return_id:
                return response['QueryExecutionId']
            else:
                data = athena.get_query_results(
                    QueryExecutionId=response['QueryExecutionId'],
                    MaxResults=1000
                )
                if queue is not None:
                    return queue.put(data['ResultSet']['Rows'])
                else:
                    return data['ResultSet']['Rows']

