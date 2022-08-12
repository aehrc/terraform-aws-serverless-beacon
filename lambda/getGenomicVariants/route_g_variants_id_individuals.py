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
from local_utils import split_query, get_split_query_fan_out
from dynamodb.datasets import Dataset
from dynamodb.variant_queries import VariantQuery, VariantResponse
import apiutils.responses as responses
import apiutils.entries as entries
from payloads.lambda_payloads import SplitQueryPayload
from payloads.lambda_responses import PerformQueryResponse
from athena.individual import Individual

SPLIT_SIZE = 1000000
BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']
SPLIT_QUERY = os.environ['SPLIT_QUERY_LAMBDA']
REQUEST_TIMEOUT = 10 # seconds 
METADATA_DATABASE = os.environ['METADATA_DATABASE']
INDIVIDUALS_TABLE = os.environ['INDIVIDUALS_TABLE']
ATHENA_WORKGROUP = os.environ['ATHENA_WORKGROUP']

dynamodb = boto3.client('dynamodb')
aws_lambda = boto3.client('lambda')
athena = boto3.client('athena')
s3 = boto3.client('s3')
requestSchemaJSON = json.load(open("requestParameters.json"))


def run_query(query):
    response = athena.start_query_execution(
        QueryString=query,
        # ClientRequestToken='string',
        QueryExecutionContext={
            'Database': METADATA_DATABASE
        },
        WorkGroup='query_workgroup'
    )

    retries = 0
    while True:
        exec = athena.get_query_execution(
            QueryExecutionId=response['QueryExecutionId']
        )
        status = exec['QueryExecution']['Status']['State']
        
        if status in ('QUEUED', 'RUNNING'):
            time.sleep(1 * (2**retries))
            retries += 1

            if retries == 4:
                print('Timed out')
                return []
            continue
        elif status in ('FAILED', 'CANCELLED'):
            print('Error: ', exec['QueryExecution']['Status'])
            return []
        else:
            data = athena.get_query_results(
                QueryExecutionId=response['QueryExecutionId'],
                # NextToken='string',
                MaxResults=1000
            )
            return Individual.parse_array(data['ResultSet']['Rows'])


# TODO break into many queries (ATHENA SQL LIMIT)
# https://docs.aws.amazon.com/athena/latest/ug/service-limits.html
def get_queries(datasetId, sampleNames):
    query = f'''
    SELECT * FROM "{METADATA_DATABASE}"."{INDIVIDUALS_TABLE}" WHERE datasetid='{datasetId}' AND samplename IN ({','.join(
        [f"'{sn}'" for sn in sampleNames]
    )});
    '''
    return query


def get_vcf_chromosome_map(all_vcfs, chromosome):
    vcf_chromosome_map = {}
    for vcf in all_vcfs:
        vcf_chromosomes = get_vcf_chromosomes(vcf)
        vcf_chromosome_map[vcf] = get_matching_chromosome(vcf_chromosomes, chromosome)
    return vcf_chromosome_map


def get_datasets(assembly_id, dataset_ids=None):
    items = []
    for item in Dataset.datasetIndex.query(assembly_id):
        items.append(item)
    # TODO support more advanced querying
    if dataset_ids:
        items = [i for i in items if i.id in dataset_ids]
    return items


def route(event):
    if (event['httpMethod'] == 'GET'):
        params = event.get('queryStringParameters', dict()) or dict()
        print(f"Query params {params}")
        apiVersion = params.get("apiVersion", BEACON_API_VERSION)
        requestedSchemas = params.get("requestedSchemas", [])
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

    variant_id = event["pathParameters"].get("id", None)
    if variant_id is None:
        return bad_request(errorMessage="Request missing variant ID")
    
    dataset_hash = base64.b64decode(variant_id.encode()).decode()
    assemblyId, referenceName, pos, referenceBases, alternateBases = dataset_hash.split('\t')
    pos = int(pos)
    datasets = get_datasets(assemblyId)
    # get vcf file and the name of chromosome in it eg: "chr1", "Chr4", "CHR1" or just "1"
    vcf_chromosomes = { vcfm.vcf: get_matching_chromosome(vcfm.chromosomes, referenceName) for dataset in datasets for vcfm in dataset.vcfChromosomeMap }
    includeResultsetResponses = 'ALL'

    start_min = pos
    start_max = pos + len(alternateBases)
    end_min = pos
    end_max = pos + len(alternateBases)

    # threading
    threads = []
    query_id = uuid4().hex

    # TODO define variant id and fix; currently consider variant id to be from a unique vcf, chrom, pos, typ
    # TODO optimise this further dataset_id -> vcfs -> vcf_id (do not use vcf index as additions and removals with 
    # make the indices inconsistent between requests)
    vcf_dataset_uuid = dict()
    dataset_variant_groups = dict()

    # record the query event on DB
    query_record = VariantQuery(query_id)
    query_record.save()
    split_query_fan_out = get_split_query_fan_out(start_min, start_max)

    # parallelism across datasets
    for dataset in datasets:
        vcf_locations = {
            vcf: vcf_chromosomes[vcf]
            for vcf in dataset.vcfLocations
            if vcf_chromosomes[vcf]
        }
        
        vcf_dataset_uuid.update({ vcf: f"{dataset.id}\t{hashlib.md5(vcf.encode()).hexdigest()}" for vcf in dataset.vcfLocations })
        # record vcf grouping information using the relevant vcf files
        vcf_groups = [
            grp for grp in [
                [loc for loc in vcfg if loc in vcf_locations]
                for vcfg in dataset.vcfGroups
            ] 
            if len(grp) > 0
        ]
        # vcf groups being searched for
        dataset_variant_groups[dataset.id] = vcf_groups

        # record perform query fan out size
        perform_query_fan_out = split_query_fan_out * len(vcf_locations)
        query_record.update(actions=[
            VariantQuery.fanOut.set(query_record.fanOut + perform_query_fan_out)
        ])

        # call split query for each dataset found
        payload = SplitQueryPayload(
                passthrough={
                    'samplesOnly': True
                },
                dataset_id=dataset.id,
                query_id=query_id,
                vcf_locations=vcf_locations,
                vcf_groups=vcf_groups,
                reference_bases=referenceBases,
                region_start=start_min,
                region_end=start_max,
                end_min=end_min,
                end_max=end_max,
                alternate_bases=alternateBases,
                variant_type=None,
                include_datasets=includeResultsetResponses,
                requested_granularity=requestedGranularity,
                variant_min_length=0,
                variant_max_length=-1
            )
        thread = threading.Thread(
                target=split_query,
                kwargs={ 'payload': payload }
            )
        thread.start()
        threads.append(thread)

    exists = False

    # wait while all the threads complete
    for thread in threads:
        thread.join()

    start_time = time.time()
    query_results = dict()
    last_read_position = 0

    while time.time() - start_time < REQUEST_TIMEOUT:
        try:
            for item in VariantResponse.variantResponseIndex.query(query_id, VariantResponse.responseNumber > last_read_position):
                query_results[item.responseNumber] = item.responseLocation
                last_read_position = item.responseNumber
            query_record.refresh()
            if query_record.fanOut == 0:
                print("Query fan in completed")
                break
        except:
            print("Errored")
            break
        time.sleep(1)

    dataset_samples = defaultdict(set)
    count = 0
    
    for _, loc in query_results.items():
        print(loc.bucket, loc.key)
        obj = s3.get_object(
            Bucket=loc.bucket,
            Key=loc.key,
        )
        query_response = jsons.loads(obj['Body'].read(), PerformQueryResponse)
        exists = exists or query_response.exists

        # immediately return the boolean response if exists
        if requestedGranularity == 'boolean' and exists:
            response = responses.get_boolean_response(exists=exists)
            response['responseSummary']['exists'] = exists
            print('Returning Response: {}'.format(json.dumps(response)))
            return bundle_response(200, response)
        else:
            exists = exists or query_response.exists
            if exists:
                exists = True
                dataset_samples[query_response.dataset_id].update(query_response.sample_names)
                count += query_response.call_count

    if requestedGranularity == 'boolean':
        response = responses.get_boolean_response(exists=exists)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if requestedGranularity == 'count':
        response = responses.get_counts_response(exists=exists, count=count)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)
    
    if requestedGranularity in ('record', 'aggregated'):
        individuals = []
        for dataset_id, sample_names in dataset_samples.items():
            if (len(sample_names)) > 0:
                individuals += run_query(get_queries(dataset_id, sample_names))

        response = responses.get_result_sets_response(
            setType='individual', 
            exists=exists,
            total=count,
            results=jsons.dump(individuals)
        )
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)


if __name__ == '__main__':
    data = {'all_alleles_count': 200, 'call_count': 100, 'dataset_id': 'test-wic', 'exists': True, 'sample_indices': [], 'sample_names': ['HG00096', 'HG00097', 'HG00099', 'HG00100', 'HG00101', 'HG00102', 'HG00103', 'HG00105', 'HG00106', 'HG00107', 'HG00108', 'HG00109', 'HG00110', 'HG00111', 'HG00112', 'HG00113', 'HG00114', 'HG00115', 'HG00116', 'HG00117', 'HG00118', 'HG00119', 'HG00120', 'HG00121', 'HG00122', 'HG00123', 'HG00125', 'HG00126', 'HG00127', 'HG00128', 'HG00129', 'HG00130', 'HG00131', 'HG00132', 'HG00133', 'HG00136', 'HG00137', 'HG00138', 'HG00139', 'HG00140', 'HG00141', 'HG00142', 'HG00143', 'HG00145', 'HG00146', 'HG00148', 'HG00149', 'HG00150', 'HG00151', 'HG00154', 'HG00155', 'HG00157', 'HG00158', 'HG00159', 'HG00160', 'HG00171', 'HG00173', 'HG00174', 'HG00176', 'HG00177', 'HG00178', 'HG00179', 'HG00180', 'HG00181', 'HG00182', 'HG00183', 'HG00185', 'HG00186', 'HG00187', 'HG00188', 'HG00189', 'HG00190', 'HG00231', 'HG00232', 'HG00233', 'HG00234', 'HG00235', 'HG00236', 'HG00237', 'HG00238', 'HG00239', 'HG00240', 'HG00242', 'HG00243', 'HG00244', 'HG00245', 'HG00246', 'HG00250', 'HG00251', 'HG00252', 'HG00253', 'HG00254', 'HG00255', 'HG00256', 'HG00257', 'HG00258', 'HG00259', 'HG00260', 'HG00261', 'HG00262'], 'variants': [], 'vcf_location': 's3://simulationexperiments/test-vcfs/100.chr5.80k.vcf.gz'}
    query = get_queries(data['dataset_id'], data['sample_names'])
    print(query)
    data = run_query(query)
    print(jsons.dump(data))