import json
import jsonschema
import boto3
import os
import base64
import hashlib

from api_response import bundle_response, bad_request
import pynamo_mappings as db
import responses
import entries


BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']
DATASETS_TABLE_NAME = os.environ['DATASETS_TABLE']
PERFORM_QUERY = os.environ['PERFORM_QUERY_LAMBDA']

dynamodb = boto3.client('dynamodb')
aws_lambda = boto3.client('lambda')
requestSchemaJSON = json.load(open("requestParameters.json"))


def perform_query(
        chrom,
        position,
        refbase,
        altbase,
        vcf_location,
        requested_granularity,
        ):

    payload = json.dumps({
        'mode': 'unique',
        'position': position,
        'chrom': chrom,
        'refbase': refbase,
        'altbase': altbase,
        'vcf_location': vcf_location,
        'requested_granularity': requested_granularity
    })

    print(f"Invoking {PERFORM_QUERY} with payload: {payload}")
    response = aws_lambda.invoke(
        FunctionName=PERFORM_QUERY,
        Payload=payload,
    )
    response_json = response['Payload'].read()
    print(f"Received payload: {response_json}")
    return json.loads(response_json)


def get_dataset(dataset_id):
    try:
        item = db.Dataset.get(dataset_id)
        return item
    except Exception as e:
        print(e)
        return None


def route(event):
    if (event['httpMethod'] == 'GET'):
        params = event.get('queryStringParameters', dict()) or dict()
        print(f"Query params {params}")
        apiVersion = params.get("apiVersion", BEACON_API_VERSION)
        requestedSchemas = params.get("requestedSchemas", [])
        includeResultsetResponses = params.get("includeResultsetResponses", 'NONE')
        requestedGranularity = params.get("requestedGranularity", "boolean")

    if (event['httpMethod'] == 'POST'):
        params = json.loads(event.get('body', "{}")) or dict()
        print(f"POST params {params}")
        meta = params.get("meta", dict())
        query = params.get("query", dict())
        # meta data
        apiVersion = meta.get("apiVersion", BEACON_API_VERSION)
        requestedSchemas = meta.get("requestedSchemas", [])
        # query data
        requestedGranularity = query.get("requestedGranularity", "boolean")
        requestParameters = query.get("requestParameters", dict())
        # validate query request
        validator = jsonschema.Draft202012Validator(requestSchemaJSON['g_variant'])
        # print(validator.schema)
        if errors := sorted(validator.iter_errors(requestParameters), key=lambda e: e.path):
            return bad_request(errorMessage= "\n".join([error.message for error in errors]))
            # raise error
        includeResultsetResponses = requestParameters.get("includeResultsetResponses", 'NONE')

    variant_id = event["pathParameters"].get("id", None)
    if variant_id is None:
        return bad_request(errorMessage="Request missing variant ID")
    
    dataset_hash = base64.b64decode(variant_id.encode()).decode()
    chrom, pos, ref, alt, typ, dataset_id, vcfMd5 = dataset_hash.split('\t')
    print(chrom, pos, ref, alt, typ, dataset_id, vcfMd5)
    pos = int(pos)
    dataset = get_dataset(dataset_id)
    vcf = None

    if not dataset:
        return bad_request(errorMessage="Invalid ID")

    # pick the vcf having the variant
    for v in dataset.vcfLocations:
        if hashlib.md5(v.encode()).hexdigest() == vcfMd5:
            vcf = v
    
    print('Params detected', chrom, pos, ref, alt, typ, dataset_id, vcf)
    variant_info = perform_query(chrom, pos, ref, alt, vcf, requestedGranularity)

    if requestedGranularity in ('record', 'aggregated'):
        result = entries.get_variant_entry(variant_id, dataset.assemblyId, ref, alt, pos, pos+len(alt), typ)
        response = responses.get_result_sets_response(reqGranularity=requestedGranularity, results=[result])
        return bundle_response(200, response)

    if requestedGranularity == 'count':
        response = responses.get_counts_response(variant_info['exists'], 1)
        return bundle_response(200, response)

    else:
        response = responses.get_boolean_response(variant_info['exists'])
        return bundle_response(200, response)