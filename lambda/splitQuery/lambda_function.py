from concurrent.futures import ThreadPoolExecutor
import json
import os
from typing import List
import gzip
import base64

import boto3

from shared.utils import LambdaClient


PERFORM_QUERY = os.environ["PERFORM_QUERY_LAMBDA"]
THREADS = 50


aws_lambda = LambdaClient()
sns = boto3.client("sns")


def perform_query(payload: dict):
    response = aws_lambda.invoke(
        FunctionName=PERFORM_QUERY,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload),
    )

    return json.loads(response["Payload"].read())


# TODO if the response is too big upload to S3
def split_query(payloads: List[dict], is_async: bool = False):
    executor = ThreadPoolExecutor(THREADS)
    futures = [executor.submit(perform_query, payload) for payload in payloads]

    return [future.result() for future in futures]


def lambda_handler(event, context):
    try:
        event = json.loads(event["Records"][0]["Sns"]["Message"])
        print("using sns event")
        is_async = True
    except:
        print("using invoke event")
        is_async = False
    
    # if gzipped
    if not isinstance(event, list):
        event = base64.b64decode(event.encode())
        event = gzip.decompress(event)
        event = json.loads(event)
    print("Event Received: {}".format(json.dumps(event)))
    response = split_query(event, is_async)
    return response


if __name__ == "__main__":
    pass
