import time
import re
import csv
import json

import boto3
from smart_open import open as sopen

from shared.ontoutils import get_ontology_details
from shared.utils import ENV_ATHENA


athena = boto3.client("athena")
pattern = re.compile(r"^\w[^:]+:.+$")

# Perform database level operations based on the queries


class AthenaModel:
    """
    This is a higher level abstraction class
    user is only required to write queries in the following form

    SELECT * FROM "{{database}}"."{{table}}" WHERE <CONDITIONS>;

    table name is fetched from the child class, database is injected
    in this class. Helps write cleaner code without so many constants
    repeated everywhere.
    """

    @classmethod
    def get_by_query(cls, query, /, *, queue=None, execution_parameters=None):
        query = query.format(database=ENV_ATHENA.ATHENA_METADATA_DATABASE, table=cls._table_name)
        exec_id = run_custom_query(
            query, queue=None, return_id=True, execution_parameters=execution_parameters
        )

        if exec_id:
            if queue is None:
                return cls.parse_array(exec_id)
            else:
                queue.put(cls.parse_array(exec_id))
        return []

    @classmethod
    def get_existence_by_query(cls, query, /, *, queue=None, execution_parameters=None):
        query = query.format(database=ENV_ATHENA.ATHENA_METADATA_DATABASE, table=cls._table_name)
        result = run_custom_query(
            query, queue=None, execution_parameters=execution_parameters
        )

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
        case_map = {k.lower(): k for k in cls().__dict__.keys()}

        with sopen(f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/query-results/{exec_id}.csv") as s3f:
            reader = csv.reader(s3f)

            for n, row in enumerate(reader):
                if n == 0:
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
    def get_count_by_query(cls, query, /, *, queue=None, execution_parameters=None):
        query = query.format(database=ENV_ATHENA.ATHENA_METADATA_DATABASE, table=cls._table_name)
        result = run_custom_query(
            query, queue=None, execution_parameters=execution_parameters
        )

        if not len(result) > 0:
            return []
        elif queue is None:
            return int(result[1]["Data"][0]["VarCharValue"])
        else:
            queue.put(int(result[1]["Data"][0]["VarCharValue"]))


def extract_terms(array):
    for item in array:
        if type(item) == dict:
            for key, value in item.items():
                if type(value) == str:
                    if key == "id" and pattern.match(value):
                        label = item.get("label", "")
                        ontology = get_ontology_details(value.split(":")[0])
                        typ = (ontology.name if ontology else "") or ""
                        yield value, label, typ
                if type(value) == dict:
                    yield from extract_terms([value])
                elif type(value) == list:
                    yield from extract_terms(value)
        if type(item) == str:
            continue
        elif type(item) == list:
            yield from extract_terms(item)


def run_custom_query(
    query,
    /,
    *,
    database=ENV_ATHENA.ATHENA_METADATA_DATABASE,
    workgroup=ENV_ATHENA.ATHENA_WORKGROUP,
    queue=None,
    return_id=False,
    execution_parameters=None,
):
    query = query.replace("\n", " ")
    print(f"{query=}")
    print(f"{execution_parameters=}")

    if execution_parameters is None:
        response = athena.start_query_execution(
            QueryString=query,
            # ClientRequestToken='string',
            QueryExecutionContext={"Database": database},
            WorkGroup=workgroup,
        )
    else:
        response = athena.start_query_execution(
            QueryString=query,
            # ClientRequestToken='string',
            QueryExecutionContext={"Database": database},
            WorkGroup=workgroup,
            ExecutionParameters=execution_parameters,
        )

    retries = 0
    while True:
        exec = athena.get_query_execution(QueryExecutionId=response["QueryExecutionId"])
        status = exec["QueryExecution"]["Status"]["State"]

        if status in ("QUEUED", "RUNNING"):
            time.sleep(0.1)
            retries += 1

            if retries == 300:
                print("Timed out")
                return None
            continue
        elif status in ("FAILED", "CANCELLED"):
            print("Error: ", exec["QueryExecution"]["Status"])
            return None
        else:
            if return_id:
                return response["QueryExecutionId"]
            else:
                data = athena.get_query_results(
                    QueryExecutionId=response["QueryExecutionId"], MaxResults=1000
                )
                if queue is not None:
                    return queue.put(data["ResultSet"]["Rows"])
                else:
                    return data["ResultSet"]["Rows"]
