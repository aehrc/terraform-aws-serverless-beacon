import os
import jsons

import boto3

from payloads.lambda_payloads import SplitQueryPayload


SPLIT_SIZE = 1000000
SPLIT_QUERY = os.environ['SPLIT_QUERY_LAMBDA']

aws_lambda = boto3.client('lambda')


def get_split_query_fan_out(region_start, region_end):
    fan_out = 0
    split_start = region_start
    while split_start <= region_end:
        fan_out += 1
        split_start += SPLIT_SIZE
    return fan_out


def split_query(payload: SplitQueryPayload):
    print(f"Invoking {SPLIT_QUERY} with payload: {jsons.dump(payload)}")
    aws_lambda.invoke(
        FunctionName=SPLIT_QUERY,
        InvocationType='Event',
        Payload=jsons.dumps(payload),
    )
