import os
import json
from typing import List

import boto3
import botocore
import jsons

from shared.payloads import PerformQueryResponse


SPLIT_SIZE = 10000
SPLIT_QUERY_LAMBDA = os.environ["SPLIT_QUERY_LAMBDA"]
SPLIT_QUERY_TOPIC_ARN = os.environ["SPLIT_QUERY_TOPIC_ARN"]

client_config = botocore.config.Config(
    max_pool_connections=500,
)
aws_lambda = boto3.client("lambda", config=client_config)
sns = boto3.client("sns")


def get_split_query_fan_out(start_min, start_max):
    fan_out = 0
    split_start = start_min
    while split_start <= start_max:
        fan_out += 1
        split_start += SPLIT_SIZE
    return fan_out


def split_query(payload: dict):
    response = aws_lambda.invoke(
        FunctionName=SPLIT_QUERY_LAMBDA,
        InvocationType="RequestResponse",
        Payload=jsons.dumps(payload),
    )
    parsed = json.loads(response["Payload"].read())
    return jsons.default_list_deserializer(parsed, List[PerformQueryResponse])
