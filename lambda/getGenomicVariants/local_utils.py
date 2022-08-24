import os
import jsons
import pickle

from smart_open import open as sopen
import boto3

from payloads.lambda_payloads import SplitQueryPayload


SPLIT_SIZE = 1000000
SPLIT_QUERY = os.environ['SPLIT_QUERY_LAMBDA']
METADATA_BUCKET = os.environ['METADATA_BUCKET']

aws_lambda = boto3.client('lambda')
onto_index_cache = None

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


def get_filtering_terms_index():
    global onto_index_cache
    if onto_index_cache is None:
        with sopen(f's3://{METADATA_BUCKET}/indexes/onto_index.pkl', 'rb') as idx:
            onto_index_cache = pickle.load(idx)
    return onto_index_cache


if __name__ == '__main__':
    print(get_filtering_terms_index())