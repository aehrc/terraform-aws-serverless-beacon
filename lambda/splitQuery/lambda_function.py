from concurrent.futures import Future, ThreadPoolExecutor
import json
import os
from typing import List

import boto3


SPLIT_SIZE = 10000
PERFORM_QUERY = os.environ["PERFORM_QUERY_LAMBDA"]
PERFORM_QUERY_TOPIC_ARN = os.environ["PERFORM_QUERY_TOPIC_ARN"]

aws_lambda = boto3.client("lambda")
sns = boto3.client("sns")


def perform_query(payload: dict):
    kwargs = {"TopicArn": PERFORM_QUERY_TOPIC_ARN, "Message": json.dumps(payload)}
    sns.publish(**kwargs)


def perform_query_sync(payload: dict):
    response = aws_lambda.invoke(
        FunctionName=PERFORM_QUERY,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload),
    )

    return json.loads(response["Payload"].read())


def split_query(split_payload: dict):
    # to find HITs or ALL we must analyse all vcfs
    split_start = split_payload.get("start_min")
    pool = ThreadPoolExecutor(32)

    while split_start <= split_payload.get("start_max"):
        split_end = min(split_start + SPLIT_SIZE - 1, split_payload.get("start_max"))
        # perform query on this split of the vcf
        for vcf_location, chrom in split_payload.get("vcf_locations", dict()).items():
            payload = {
                "query_id": split_payload.get("query_id"),
                "reference_bases": split_payload.get("reference_bases"),
                "alternate_bases": split_payload.get("alternate_bases"),
                "end_min": split_payload.get("end_min"),
                "end_max": split_payload.get("end_max"),
                "variant_type": split_payload.get("variant_type"),
                "requested_granularity": split_payload.get("requested_granularity"),
                "variant_min_length": split_payload.get("variant_min_length"),
                "variant_max_length": split_payload.get("variant_max_length"),
                "include_details": split_payload.get("include_datasets", "ALL")
                in ("HIT", "ALL"),
                "region": f"{chrom}:{split_start}-{split_end}",
                "vcf_location": vcf_location,
            }
            pool.submit(perform_query, payload)

        # next split
        split_start += SPLIT_SIZE

    pool.shutdown()


def split_query_sync(split_payload: dict):
    # to find HITs or ALL we must analyse all vcfs
    split_start = split_payload.get("start_min")
    pool = ThreadPoolExecutor(32)
    futures: List[Future] = []

    while split_start <= split_payload.get("start_max"):
        split_end = min(split_start + SPLIT_SIZE - 1, split_payload.get("start_max"))
        # perform query on this split of the vcf
        for vcf_location, chrom in split_payload.get("vcf_locations", dict()).items():
            payload = {
                "query_id": split_payload.get("query_id"),
                "dataset_id": split_payload.get("dataset_id"),
                "samples": split_payload.get("samples", []),
                "reference_bases": split_payload.get("reference_bases"),
                "alternate_bases": split_payload.get("alternate_bases"),
                "end_min": split_payload.get("end_min"),
                "end_max": split_payload.get("end_max"),
                "variant_min_length": split_payload.get("variant_min_length"),
                "variant_max_length": split_payload.get("variant_max_length"),
                "include_details": split_payload.get("include_datasets", "ALL")
                in ("HIT", "ALL"),
                "include_samples": split_payload.get("include_samples", False),
                "region": f"{chrom}:{split_start}-{split_end}",
                "vcf_location": vcf_location,
                "variant_type": split_payload.get("variant_type"),
                "requested_granularity": split_payload.get("requested_granularity"),
            }
            futures.append(pool.submit(perform_query_sync, payload))

        # next split
        split_start += SPLIT_SIZE

    return [future.result() for future in futures]


def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))

    try:
        event = json.loads(event["Records"][0]["Sns"]["Message"])
        print("using sns event")
        print(event)
        split_query(event)
        print("Completed split query")
    except:
        print("using invoke event")
        response = split_query_sync(event)

        return response


if __name__ == "__main__":
    pass
