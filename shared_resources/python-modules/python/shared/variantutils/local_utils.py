import os
import json
import queue

import boto3
import jsons

from shared.payloads.lambda_payloads import SplitQueryPayload


SPLIT_SIZE = 10000
SPLIT_QUERY = os.environ["SPLIT_QUERY_LAMBDA"]
SPLIT_QUERY_TOPIC_ARN = os.environ["SPLIT_QUERY_TOPIC_ARN"]

aws_lambda = boto3.client("lambda")
sns = boto3.client("sns")


def get_split_query_fan_out(start_min, start_max):
    fan_out = 0
    split_start = start_min
    while split_start <= start_max:
        fan_out += 1
        split_start += SPLIT_SIZE
    return fan_out


def split_query(payload: SplitQueryPayload):
    kwargs = {"TopicArn": SPLIT_QUERY_TOPIC_ARN, "Message": jsons.dumps(payload)}

    sns.publish(**kwargs)


def split_query_sync(payload: SplitQueryPayload, results_queue: queue.Queue):
    response = aws_lambda.invoke(
        FunctionName=SPLIT_QUERY,
        InvocationType="RequestResponse",
        Payload=jsons.dumps(payload),
    )

    results_queue.put(json.loads(response["Payload"].read()))
