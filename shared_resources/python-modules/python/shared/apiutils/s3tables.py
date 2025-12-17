import time

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from shared.payloads import PerformQueryResponse


def info_to_json(info_str: str):
    # input {AA=G, AC=22, SAS_AF=0, AF=0.0178427, NS=1233, EX_TARGET=true, DP=84761, AN=1233, AMR_AF=0, EUR_AF=0, EAS_AF=0.0902, AFR_AF=0, VT=SNP}
    info_dict = {}
    info_str_stripped = info_str.strip("{}")
    for item in info_str_stripped.split(", "):
        key, value = item.strip().split("=", 1)
        info_dict[key] = value

        # if numeric, convert to int or float
        if value.isdigit():
            info_dict[key] = int(value)
        elif value.replace(".", "", 1).isdigit():
            info_dict[key] = float(value)
    return info_dict


def fetch_results(query_execution_id: str, max_rows: int = 10000):
    """Retrieve up to max_rows result rows (including header)."""
    client = boto3.client("athena")
    rows = []
    next_token = None
    while True and len(rows) < max_rows:
        params = {"QueryExecutionId": query_execution_id}
        if next_token:
            params["NextToken"] = next_token
        resp = client.get_query_results(**params)
        for row in resp.get("ResultSet", {}).get("Rows", []):
            rows.append(
                [datum.get("VarCharValue", "") for datum in row.get("Data", [])]
            )
            if len(rows) >= max_rows:
                break
        next_token = resp.get("NextToken")
        if not next_token or len(rows) >= max_rows:
            break
    headers = rows[0]
    data_rows = rows[1:] if len(rows) > 1 else []
    json_entries = [dict(zip(headers, r)) for r in data_rows]

    print(f"{json_entries=}")

    for i, _ in enumerate(json_entries):
        if "info" in json_entries[i]:
            info_dict = info_to_json(json_entries[i]["info"])
            json_entries[i]["info"] = info_dict

    print(f"{json_entries=}")

    response = PerformQueryResponse(
        dataset_id="_",
        exists=len(json_entries) > 0,
        all_alleles_count=sum(
            int(entry.get("info", {}).get("AN", 0)) for entry in json_entries
        ),
        variants=[
            f"{entry['chrom']}\t{entry['pos']}\t{entry['ref']}\t{entry['alt']}\t{entry['info']['VT']}"
            for entry in json_entries
        ],
        call_count=sum(
            sum((map(int, str(entry.get("info", {}).get("AC", "0")).split(","))))
            for entry in json_entries
        ),
        sample_names=[],
    )
    return response


def wait_for_completion(
    query_execution_id: str,
    timeout_seconds: int = 180,
    poll_interval: float = 2.5,
) -> str:
    """Poll Athena until terminal state or timeout."""
    client = boto3.client("athena")
    deadline = time.time() + timeout_seconds
    last_state = ""
    while time.time() < deadline:
        try:
            resp = client.get_query_execution(QueryExecutionId=query_execution_id)
        except (BotoCoreError, ClientError) as e:
            print(f"Error retrieving query execution status: {e}")
            time.sleep(poll_interval)
            continue
        state = resp["QueryExecution"]["Status"]["State"]
        if state != last_state:
            print(f"Query state: {state}")
            last_state = state
        if state in {"SUCCEEDED", "FAILED", "CANCELLED"}:
            return state
        time.sleep(poll_interval)
    print("Timeout waiting for Athena query to complete")
    return last_state or "UNKNOWN"


def perform_variant_search_s3tables(
    reference_name,
    reference_bases,
    alternate_bases,
    start,
    end,
    samples,
):
    if not samples:
        query = """
            SELECT *
            FROM "variant_db"."variants" v
            WHERE v.chrom = ?
                AND v.pos BETWEEN ? AND ?
            ORDER BY v.pos
        """
        client = boto3.client("athena")
        params = dict(
            QueryString=query,
            QueryExecutionContext={
                "Database": "variant_db",
                "Catalog": "s3tablescatalog/wic053-variantstore-schema-1",
            },
            WorkGroup="primary",
            ResultConfiguration={
                "OutputLocation": "s3://wic053-s3-table-bucket-results-bucket-syd/"
            },
            ExecutionParameters=[
                (
                    f"'{reference_name}'"
                    if str(reference_name).isnumeric()
                    else reference_name
                ),
                str(start[0] + 1),
                str(end[0]),
            ],
        )
    print("Starting Athena query execution with parameters:", params)
    response = client.start_query_execution(**params)
    exec_id = response["QueryExecutionId"]
    state = wait_for_completion(exec_id, timeout_seconds=300, poll_interval=1.0)

    if state != "SUCCEEDED":
        return []
    return [fetch_results(exec_id)]


def fetch_results2(query_execution_id: str, max_rows: int = 10000):
    """Retrieve up to max_rows result rows (including header)."""
    client = boto3.client("athena")
    rows = []
    next_token = None
    while True and len(rows) < max_rows:
        params = {"QueryExecutionId": query_execution_id}
        if next_token:
            params["NextToken"] = next_token
        resp = client.get_query_results(**params)
        for row in resp.get("ResultSet", {}).get("Rows", []):
            rows.append(
                [datum.get("VarCharValue", "") for datum in row.get("Data", [])]
            )
            if len(rows) >= max_rows:
                break
        next_token = resp.get("NextToken")
        if not next_token or len(rows) >= max_rows:
            break
    headers = rows[0]
    data_rows = rows[1:] if len(rows) > 1 else []
    json_entries = [dict(zip(headers, r)) for r in data_rows]

    return json_entries


def perform_sample_search_s3tables(
    reference_name,
    reference_bases,
    alternate_bases,
    pos,
    samples,
):
    query = """
        SELECT s.sample_name
        FROM "variant_db"."variants" v
            INNER JOIN "variant_db"."variant_samples" vs ON v.variant_id = vs.variant_id
            INNER JOIN "variant_db"."samples" s ON vs.sample_id = s.sample_id
        WHERE v.chrom = ?
            AND v.pos = ?
            AND v.ref = ?
            AND v.alt = ?
            AND vs.genotype != '0|0'
    """
    if len(samples) > 0:
        query += f"""
            AND s.sample_name IN ({','.join([f"'{sn}'" for sn in samples])})
        """
    print(query)
    client = boto3.client("athena")
    params = dict(
        QueryString=query,
        QueryExecutionContext={
            "Database": "variant_db",
            "Catalog": "s3tablescatalog/wic053-variantstore-schema-1",
        },
        WorkGroup="primary",
        ResultConfiguration={
            "OutputLocation": "s3://wic053-s3-table-bucket-results-bucket-syd/"
        },
        ExecutionParameters=[
            (
                f"'{reference_name}'"
                if str(reference_name).isnumeric()
                else reference_name
            ),
            str(pos),
            reference_bases,
            alternate_bases,
        ],
    )
    print("Starting Athena query execution with parameters:", params)
    response = client.start_query_execution(**params)
    exec_id = response["QueryExecutionId"]
    state = wait_for_completion(exec_id, timeout_seconds=300, poll_interval=1.0)

    if state != "SUCCEEDED":
        return []
    return fetch_results2(exec_id)
