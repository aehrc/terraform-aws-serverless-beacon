from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import threading
import time
import json

from smart_open import open as sopen
import boto3

from shared.dynamodb import Descendants, Anscestors, Ontology, TermLabels
from shared.ontoutils import request_hierarchy
from shared.apiutils import bundle_response
from shared.utils import ENV_ATHENA, ENV_SNS
from ctas_queries import QUERY as CTAS_TEMPLATE
from generate_query_index import QUERY as INDEX_QUERY
from generate_query_terms import QUERY as TERMS_QUERY
from generate_query_relations import QUERY as RELATIONS_QUERY


athena = boto3.client("athena")
s3 = boto3.client("s3")
sns = boto3.client("sns")


ENSEMBL_OLS = "https://www.ebi.ac.uk/ols/api/ontologies"
ONTOSERVER = "https://r4.ontoserver.csiro.au/fhir/ValueSet/$expand"
ONTO_TERMS_QUERY = f""" SELECT term,tablename,colname,type,label FROM "{ENV_ATHENA.ATHENA_TERMS_TABLE}" """
INDEX_QUERY = INDEX_QUERY.format(
    table=ENV_ATHENA.ATHENA_TERMS_CACHE_TABLE,
    uri=f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/terms-index/",
)
TERMS_QUERY = TERMS_QUERY.format(
    table=ENV_ATHENA.ATHENA_TERMS_CACHE_TABLE,
    uri=f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/terms/",
)
RELATIONS_QUERY = RELATIONS_QUERY.format(
    uri=f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/relations/",
    individuals_table=ENV_ATHENA.ATHENA_INDIVIDUALS_TABLE,
    biosamples_table=ENV_ATHENA.ATHENA_BIOSAMPLES_TABLE,
    runs_table=ENV_ATHENA.ATHENA_RUNS_TABLE,
    analyses_table=ENV_ATHENA.ATHENA_ANALYSES_TABLE,
)


def get_ontologie_terms_in_beacon():
    query = f'SELECT DISTINCT term FROM "{ENV_ATHENA.ATHENA_TERMS_TABLE}"'

    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": ENV_ATHENA.ATHENA_METADATA_DATABASE},
        WorkGroup=ENV_ATHENA.ATHENA_WORKGROUP,
    )

    execution_id = response["QueryExecutionId"]
    await_result(execution_id)

    ontology_terms = list()

    with sopen(
        f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/query-results/{execution_id}.csv"
    ) as s3f:
        for n, line in enumerate(s3f):
            if n == 0:
                continue
            term = line.strip().strip('"')
            ontology_terms.append(term)
    return ontology_terms


# TODO in future, there could be an issue when descendants entries exceed 400KB
# which means we would have roughtly 20480, 20 byte entries (unlikely?)
# this would also mean, our SQL queries would reach the 256KB limit
# we should be able to easily spread terms across multiple dynamodb
# entries and have multiple queries (as recommended by AWS)
def index_terms_tree():
    terms_in_beacon = get_ontologie_terms_in_beacon()
    executor = ThreadPoolExecutor(500)
    futures = []

    for term in terms_in_beacon:
        try:
            Anscestors.get(term)
        except Anscestors.DoesNotExist:
            futures.append(executor.submit(request_hierarchy, term, True))

    # record ancestors
    term_anscestors = defaultdict(set)
    # record term labels
    term_label = dict()

    for future in as_completed(futures):
        term, ancestors_dict = future.result()

        if ancestors_dict:
            term_anscestors[term].update(list(ancestors_dict.keys()))
            term_anscestors[term].add(term)
            term_label.update(ancestors_dict)

    # reverse the tree for descendent term search
    term_descendants = defaultdict(set)

    # write ancestors
    with Anscestors.batch_write() as batch:
        for term, anscestors in term_anscestors.items():
            item = Anscestors(term)
            item.anscestors = anscestors
            batch.save(item)

            # record descendents
            for anscestor in anscestors:
                term_descendants[anscestor].add(term)

    # write descendents
    with Descendants.batch_write() as batch:
        for term, descendants in term_descendants.items():
            # if descendants are recorded, just update, else make record
            try:
                item = Descendants.get(term)
                item.update(actions=[Descendants.descendants.add(descendants)])
            except Descendants.DoesNotExist:
                item = Descendants(term)
                item.descendants = descendants
                batch.save(item)

    # write term labels
    with TermLabels.batch_write() as batch:
        for term, label in term_label.items():
            item = TermLabels(term)
            item.label = label
            batch.save(item)


def update_athena_partitions(table):
    athena.start_query_execution(
        QueryString=f"MSCK REPAIR TABLE `{table}`",
        # ClientRequestToken='string',
        QueryExecutionContext={"Database": ENV_ATHENA.ATHENA_METADATA_DATABASE},
        WorkGroup=ENV_ATHENA.ATHENA_WORKGROUP,
    )


def await_result(execution_id, sleep=2):
    retries = 0
    while True:
        exec = athena.get_query_execution(QueryExecutionId=execution_id)
        status = exec["QueryExecution"]["Status"]["State"]

        if status in ("QUEUED", "RUNNING"):
            time.sleep(sleep)
            retries += 1

            if retries == 60:
                print("Timed out")
                return []
            continue
        elif status in ("FAILED", "CANCELLED"):
            print("Error: ", exec["QueryExecution"]["Status"])
            raise Exception("Error: " + str(exec["QueryExecution"]["Status"]))
        elif status == "SUCCEEDED":
            return


def drop_tables(table):
    query = f"DROP TABLE IF EXISTS {table};"
    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": ENV_ATHENA.ATHENA_METADATA_DATABASE},
        WorkGroup=ENV_ATHENA.ATHENA_WORKGROUP,
    )
    await_result(response["QueryExecutionId"])


def clean_files(bucket, prefix):
    has_more = True
    while has_more:
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        files_to_delete = []
        for object in response.get("Contents", []):
            files_to_delete.append({"Key": object["Key"]})
        if files_to_delete:
            s3.delete_objects(Bucket=bucket, Delete={"Objects": files_to_delete})
        has_more = response["IsTruncated"]
    time.sleep(1)


def ctas_basic_tables(
    *, source_table, destination_table, destination_prefix, bucket_count, bucket_by
):
    clean_files(ENV_ATHENA.ATHENA_METADATA_BUCKET, destination_prefix)
    drop_tables(destination_table)

    query = CTAS_TEMPLATE.format(
        target=destination_table,
        uri=f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/{destination_prefix}",
        bucket_by=bucket_by,
        table=source_table,
        bucket_count=bucket_count,
    )
    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": ENV_ATHENA.ATHENA_METADATA_DATABASE},
        WorkGroup=ENV_ATHENA.ATHENA_WORKGROUP,
    )
    await_result(response["QueryExecutionId"])


def index_terms():
    clean_files(ENV_ATHENA.ATHENA_METADATA_BUCKET, "terms-index/")
    drop_tables(ENV_ATHENA.ATHENA_TERMS_INDEX_TABLE)

    response = athena.start_query_execution(
        QueryString=INDEX_QUERY,
        QueryExecutionContext={"Database": ENV_ATHENA.ATHENA_METADATA_DATABASE},
        WorkGroup=ENV_ATHENA.ATHENA_WORKGROUP,
    )
    await_result(response["QueryExecutionId"])


def record_terms():
    clean_files(ENV_ATHENA.ATHENA_METADATA_BUCKET, "terms/")
    drop_tables(ENV_ATHENA.ATHENA_TERMS_TABLE)

    response = athena.start_query_execution(
        QueryString=TERMS_QUERY,
        QueryExecutionContext={"Database": ENV_ATHENA.ATHENA_METADATA_DATABASE},
        WorkGroup=ENV_ATHENA.ATHENA_WORKGROUP,
    )
    await_result(response["QueryExecutionId"])


def record_relations():
    clean_files(ENV_ATHENA.ATHENA_METADATA_BUCKET, "relations/")
    drop_tables(ENV_ATHENA.ATHENA_RELATIONS_TABLE)

    response = athena.start_query_execution(
        QueryString=RELATIONS_QUERY,
        QueryExecutionContext={"Database": ENV_ATHENA.ATHENA_METADATA_DATABASE},
        WorkGroup=ENV_ATHENA.ATHENA_WORKGROUP,
    )
    await_result(response["QueryExecutionId"])


def reindex_tables():
    # CTAS this must finish before all
    threads = []
    for src, dest, prefix, bucket_count, bucket_by in (
        (
            ENV_ATHENA.ATHENA_DATASETS_CACHE_TABLE,
            ENV_ATHENA.ATHENA_DATASETS_TABLE,
            "datasets/",
            10,
            "'id', '_assemblyid'",
        ),
        (
            ENV_ATHENA.ATHENA_COHORTS_CACHE_TABLE,
            ENV_ATHENA.ATHENA_COHORTS_TABLE,
            "cohorts/",
            10,
            "'id'",
        ),
        (
            ENV_ATHENA.ATHENA_INDIVIDUALS_CACHE_TABLE,
            ENV_ATHENA.ATHENA_INDIVIDUALS_TABLE,
            "individuals/",
            50,
            "'id', '_datasetid'",
        ),
        (
            ENV_ATHENA.ATHENA_BIOSAMPLES_CACHE_TABLE,
            ENV_ATHENA.ATHENA_BIOSAMPLES_TABLE,
            "biosamples/",
            50,
            "'id', '_datasetid'",
        ),
        (
            ENV_ATHENA.ATHENA_RUNS_CACHE_TABLE,
            ENV_ATHENA.ATHENA_RUNS_TABLE,
            "runs/",
            50,
            "'id', '_datasetid'",
        ),
        (
            ENV_ATHENA.ATHENA_ANALYSES_CACHE_TABLE,
            ENV_ATHENA.ATHENA_ANALYSES_TABLE,
            "analyses/",
            50,
            "'id', '_datasetid'",
        ),
    ):
        threads.append(
            threading.Thread(
                target=ctas_basic_tables,
                kwargs={
                    "source_table": src,
                    "destination_table": dest,
                    "destination_prefix": prefix,
                    "bucket_count": bucket_count,
                    "bucket_by": bucket_by,
                },
            )
        )
        threads[-1].start()
    [thread.join() for thread in threads]


def clean_onto_index_tables():
    with Anscestors.batch_write() as batch:
        for entry in Anscestors.scan():
            batch.delete(entry)
    with Descendants.batch_write() as batch:
        for entry in Descendants.scan():
            batch.delete(entry)
    with Ontology.batch_write() as batch:
        for entry in Ontology.scan():
            batch.delete(entry)
    with TermLabels.batch_write() as batch:
        for entry in TermLabels.scan():
            batch.delete(entry)


def lambda_handler(event, context):
    body_dict = dict()

    # API call
    if event.get("httpMethod", "") == "POST":
        try:
            body_dict = json.loads(event.get("body") or "{}")
        except ValueError:
            # fallback to defaul behaviour
            body_dict = dict()
        kwargs = {
            "TopicArn": ENV_SNS.INDEXER_TOPIC_ARN,
            "Message": json.dumps(body_dict),
        }
        print("Publishing to SNS: {}".format(json.dumps(kwargs)))
        sns.publish(**kwargs)

        return bundle_response(
            200,
            {
                "success": True,
                "message": "Running indexer asynchronously. Indexer may take upto few minutes.",
            },
        )
    # SNS
    elif "Sns" in event.get("Records", ["None"])[0]:
        body_dict = json.loads(event["Records"][0]["Sns"]["Message"])
    # Local
    else:
        body_dict = event

    re_index_tables = body_dict.get("reIndexTables", True)
    re_index_ontology_tables = body_dict.get("reIndexOntologyTerms", False)

    # re-index all tables using CTAS
    if re_index_tables:
        reindex_tables()

    # cleanup recorded terms in DynamoDB
    if re_index_ontology_tables:
        clean_onto_index_tables()

    # index terms and corresponding entity type and id they appear
    index_thread = None
    if re_index_tables:
        index_thread = threading.Thread(target=index_terms)
        index_thread.start()

    # the massive JOIN operation between all tables to create the links
    relations_thread = None

    if re_index_tables:
        relations_thread = threading.Thread(target=record_relations)
        relations_thread.start()

    # create the global terms table with term, label, type and kind
    # derived from terms cache discarding entity ids
    if body_dict.get("reIndexTables", True):
        record_terms()

    # build ontology tree
    index_terms_tree()

    # join last running threads
    if re_index_tables:
        index_thread.join()
        relations_thread.join()

    print("Indexing complete!")


if __name__ == "__main__":
    lambda_handler({"reIndexTables": True, "reIndexOntologyTerms": True}, {})
    pass
