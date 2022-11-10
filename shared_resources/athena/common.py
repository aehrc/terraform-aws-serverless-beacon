import boto3
import os
import time
import re
import csv
import json

from smart_open import open as sopen

from dynamodb.ontologies import expand_terms


METADATA_BUCKET = os.environ['METADATA_BUCKET']
ATHENA_WORKGROUP = os.environ['ATHENA_WORKGROUP']
METADATA_DATABASE = os.environ['METADATA_DATABASE']
TERMS_INDEX_TABLE = os.environ['TERMS_INDEX_TABLE']
RELATIONS_TABLE = os.environ['RELATIONS_TABLE']

athena = boto3.client('athena')
pattern = re.compile(f'^\\w[^:]+:.+$')

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
        exec_id = run_custom_query(query, METADATA_DATABASE, ATHENA_WORKGROUP, queue=None, return_id=True)

        if exec_id:
            if queue is None:
                return cls.parse_array(exec_id)
            else:
                queue.put(cls.parse_array(exec_id))
        return []

    
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
    def parse_array(cls, exec_id):
        instances = []
        var_list = list()
        case_map = { k.lower(): k for k in cls().__dict__.keys() }

        with sopen(f's3://{METADATA_BUCKET}/query-results/{exec_id}.csv') as s3f:
            reader = csv.reader(s3f)

            for n, row in enumerate(reader):
                if n==0:
                    var_list = row
                else:
                    instance = cls()
                    for attr, val in zip(var_list, row):
                        if not attr in case_map:
                            continue
                        try:
                            val = json.loads(val)
                        except:
                            val = val
                        instance.__dict__[case_map[attr]] = val
                    instances.append(instance)

        return instances


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


def extract_terms(array):
    for item in array:
        if type(item) == dict:
            label = item.get('label', '')
            typ = item.get('type', 'string')
            for key, value in item.items():
                if type(value) == str:
                    if key == "id" and pattern.match(value):
                        yield value, label, typ
                if type(value) == dict:
                    yield from extract_terms([value])
                elif type(value) == list:
                    yield from extract_terms(value)
        if type(item) == str:
            continue
        elif type(item) == list:
            yield from extract_terms(item)


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
                return None
            continue
        elif status in ('FAILED', 'CANCELLED'):
            print('Error: ', exec['QueryExecution']['Status'])
            return None
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


def entity_search_conditions(filters, id_type, default_scope, id_modifier='id', with_where=True):
    types = {'individuals', 'biosamples', 'runs', 'analyses', 'datasets', 'cohorts'} - { default_scope }
    type_relations_table_id = {
        'individuals': 'individualid',
        'biosamples': 'biosampleid',
        'runs': 'runid',
        'analyses': 'analysisid',
        'datasets': 'datasetid',
        'cohorts': 'cohortid'
    }

    conditions = []
    default_scope_filters = list(filter(lambda x: x.get('scope', default_scope) == default_scope, filters))
        
    if default_scope_filters:
        expanded_terms = expand_terms(default_scope_filters)
        conditions += [f''' {id_modifier} IN (SELECT RI.{type_relations_table_id[id_type]} FROM "{RELATIONS_TABLE}" RI JOIN "{TERMS_INDEX_TABLE}" TI ON RI.{type_relations_table_id[default_scope]} = TI.id where TI.kind='{default_scope}' and TI.term IN ({expanded_terms})) ''']

    for group in types:
        group_filters = list(filter(lambda x: x.get('scope') == group, filters))
        
        if group_filters:
            expanded_terms = expand_terms(group_filters)
            conditions += [f''' {id_modifier} IN (SELECT RI.{type_relations_table_id[id_type]} FROM "{RELATIONS_TABLE}" RI JOIN "{TERMS_INDEX_TABLE}" TI ON RI.{type_relations_table_id[group]} = TI.id where TI.kind='{group}' and TI.term IN ({expanded_terms})) ''']
        
    if conditions:
        if with_where:
            return 'WHERE ' + ' AND '.join(conditions)
        else:
            return ' AND '.join(conditions)
    return ''