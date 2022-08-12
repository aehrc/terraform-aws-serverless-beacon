from collections import defaultdict
import json
import jsonschema
import queue
import threading
import boto3
import os
import hashlib
import base64
import jsons
from uuid import uuid4
import time

from apiutils.api_response import bundle_response, bad_request
from utils.chrom_matching import get_matching_chromosome, get_vcf_chromosomes
from dynamodb.datasets import Dataset
from dynamodb.variant_queries import VariantQuery, VariantResponse
import apiutils.responses as responses
import apiutils.entries as entries
from payloads.lambda_payloads import SplitQueryPayload
from payloads.lambda_responses import PerformQueryResponse


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