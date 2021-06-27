import json
from math import ceil
import os
import re
import subprocess
import time

import boto3
from botocore.exceptions import ClientError

ASSEMBLY_GSI = os.environ['ASSEMBLY_GSI']
DATASETS_TABLE_NAME = os.environ['DATASETS_TABLE']
SUMMARISE_DATASET_SNS_TOPIC_ARN = os.environ['SUMMARISE_DATASET_SNS_TOPIC_ARN']
SUMMARISE_SLICE_SNS_TOPIC_ARN = os.environ['SUMMARISE_SLICE_SNS_TOPIC_ARN']
VCF_SUMMARIES_TABLE_NAME = os.environ['VCF_SUMMARIES_TABLE']

# If only this much time remains, split the task
MILLISECONDS_BEFORE_SPLIT = 15000

# How many records between each performance sample
RECORDS_PER_SAMPLE = 10000

os.environ['PATH'] += ':' + os.environ['LAMBDA_TASK_ROOT']

dynamodb = boto3.client('dynamodb')
sns = boto3.client('sns')

all_count_pattern = re.compile('[0-9]+')
get_all_calls = all_count_pattern.findall


def calculate_slices(location, chrom, start, end, num_slices):
    start_pos_exc = start - 1  # Won't include the first position, so step back
    total_size = end - start_pos_exc
    min_size = total_size // num_slices
    remainder = total_size % num_slices
    slices = []
    for slice_number in range(num_slices):
        slice_size = min_size
        if remainder > 0:
            slice_size += 1
            remainder -= 1
        slices.append({
            'location': location,
            'region': '{}:{}'.format(
                chrom, start_pos_exc),
            'slice_size': slice_size
        })
        start_pos_exc += slice_size
    return slices


def get_affected_datasets(location):
    kwargs = {
        'TableName': DATASETS_TABLE_NAME,
        'IndexName': ASSEMBLY_GSI,
        'ProjectionExpression': 'id',
        'FilterExpression': 'contains(vcfLocations, :location)',
        'ExpressionAttributeValues': {
            ':location': {
                'S': location,
            },
        },
    }
    dataset_ids = []
    still_to_scan = True
    while still_to_scan:
        print("Scanning table: {}".format(json.dumps(kwargs)))
        response = dynamodb.scan(**kwargs)
        print("Received response: {}".format(json.dumps(response)))
        dataset_ids += [item['id']['S'] for item in response.get('Items', [])]
        last_evaluated_key = response.get('LastEvaluatedKey')
        if last_evaluated_key:
            kwargs['ExclusiveStartKey'] = last_evaluated_key
        else:
            still_to_scan = False
    return dataset_ids


def get_calls_and_variants(location, chrom, start, end, time_assigned,
                           gvcf=False):

    counts_process = get_counts_process(location, chrom, start, end,
                                        gvcf=gvcf)
    counts_handle = counts_process.stdout
    call_count, variant_count, slices = sum_counts(counts_handle, start, end,
                                                   time_assigned, gvcf=gvcf)
    counts_handle.close()
    error_code = counts_process.wait(timeout=1)
    if error_code != 0 and not slices:  # complains when pipe is closed
        if not gvcf:
            # Process errored out, could be because INFO tags aren't defined.
            # This happens in the case of gVCFs, so try again using only GT.
            print("Got error when querying, trying gVCF mode...")
            call_count, variant_count, slices = get_calls_and_variants(
                location, chrom, start, end, time_assigned, gvcf=True)
        else:
            assert error_code == 0, ("query returned error code"
                                     " {}".format(error_code))
    return call_count, variant_count, slices


def get_counts_process(location, chrom, start, end, gvcf=False):
    args = [
        'bcftools', 'query',
        '--regions', '{chrom}:{start}-{end}'.format(
            chrom=chrom, start=start, end=end),
        '--format', '%POS\t[%GT,]\n' if gvcf else '%POS\t%INFO/AN\t%INFO/AC\n',
        location
    ]
    query_process = subprocess.Popen(args, stdout=subprocess.PIPE, cwd='/tmp',
                                     encoding='ascii')
    return query_process


def get_slices_to_complete(time_assigned, start_time, start, end, current_pos):
    """
    Calculate the number of slices that will be required to complete the task
    in time.
    """
    fraction_complete = (current_pos - start) / (end - start + 1)
    if not fraction_complete:
        # Just return, if we can't get through a single position, we have larger
        # problems.
        return None
    time_passed = (time.time() - start_time) * 1000
    time_to_complete = time_passed / fraction_complete
    slices = ceil(time_to_complete / time_assigned)
    return slices


def publish_slice_updates(slice_data):
    kwargs = {
        'TopicArn': SUMMARISE_SLICE_SNS_TOPIC_ARN,
    }
    for slice_datum in slice_data:
        kwargs['Message'] = json.dumps(slice_datum)
        print('Publishing to SNS: {}'.format(json.dumps(kwargs)))
        response = sns.publish(**kwargs)
        print('Received Response: {}'.format(json.dumps(response)))


def update_vcf(location, region, variant_count, call_count, to_add=None):
    kwargs = {
        'TableName': VCF_SUMMARIES_TABLE_NAME,
        'Key': {
            'vcfLocation': {
                'S': location,
            },
        },
        'UpdateExpression': 'ADD variantCount :variantCount,'
                            '    callCount :callCount',
        'ExpressionAttributeValues': {
            ':variantCount': {
                'N': str(variant_count),
            },
            ':callCount': {
                'N': str(call_count),
            },
            ':region': {
                'S': region,
            },
        },
        'ConditionExpression': 'contains(toUpdate, :region)',
    }
    if to_add:
        kwargs['UpdateExpression'] += ', toUpdate :regionSet'
        kwargs['ExpressionAttributeValues'][':regionSet'] = {'SS': to_add}
    else:
        kwargs['UpdateExpression'] += ' DELETE toUpdate :regionSet'
        kwargs['ExpressionAttributeValues'][':regionSet'] = {'SS': [region]}
        kwargs['ReturnValues'] = 'UPDATED_NEW'

    print('Updating table: {}'.format(json.dumps(kwargs)))
    try:
        response = dynamodb.update_item(**kwargs)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            print("VCF region has already been recorded, aborting.")
            return False
        else:
            raise e
    if not to_add and response['Attributes'].get('toUpdate'):
        return False
    else:
        return True


def summarise_datasets(datasets):
    kwargs = {
        'TopicArn': SUMMARISE_DATASET_SNS_TOPIC_ARN,
    }
    for dataset in datasets:
        kwargs['Message'] = dataset
        print('Publishing to SNS: {}'.format(json.dumps(kwargs)))
        response = sns.publish(**kwargs)
        print('Received Response: {}'.format(json.dumps(response)))


def sum_counts(counts_handle, start, end, time_assigned, gvcf=False):
    call_count = 0
    variant_count = 0
    records = 0
    start_time = 0
    next_sample_record = 0
    for record in counts_handle:
        record_parts = record.split('\t')
        pos = int(record_parts[0])

        # Only count records that start directly in the query range
        if not start <= pos <= end:
            continue

        # Check if the records are being processed fast enough
        if records == next_sample_record:
            next_sample_record += RECORDS_PER_SAMPLE
            if start_time == 0:
                start_time = time.time()
                print("starting timer at {}".format(start_time))
            else:
                slices = get_slices_to_complete(time_assigned, start_time,
                                                start, end, pos)
                if slices > 1:
                    return None, None, slices
        records += 1

        if gvcf:
            genotype_str = record_parts[1]
            # As AN is often not present, simply manually count all the calls
            calls = get_all_calls(genotype_str)
            call_count += len(calls)
            # Add number of unique non-reference calls to variant count
            call_set = set(calls)
            variant_count += len(call_set) - (1 if '0' in call_set else 0)
        else:
            call_num_str, alt_allele_num_str = (record_parts[1],
                                                record_parts[2].rstrip('\r\n'))
            # Add the AN value to the call count
            call_count += int(call_num_str)
            # Add the total number of alt alleles with nonzero counts to variant
            # count
            variant_count += sum(1 for alt in alt_allele_num_str.split(',')
                                 if int(alt))
    return call_count, variant_count, None


def summarise_slice(location, region, slice_size, time_assigned):
    chrom, start_str = region.split(':')
    start = int(start_str)
    end = start + slice_size - 1
    call_count, variant_count, slices = get_calls_and_variants(
        location, chrom, start, end, time_assigned)
    if call_count is not None:
        update_complete = update_vcf(location, region, variant_count, call_count)
        if update_complete:
            print('Final slice summarised.')
            impacted_datasets = get_affected_datasets(location)
            summarise_datasets(impacted_datasets)
    else:
        print("Assigned time of {time} is not sufficent. Splitting into"
              " {slices} slices.".format(time=time_assigned, slices=slices))
        slice_data = calculate_slices(location, chrom, start, end, slices)
        no_error = update_vcf(location, region, 0, 0,
                              # Don't add first region - it should already be
                              # there
                              to_add=[s['region'] for s in slice_data[1:]])
        if no_error:
            publish_slice_updates(slice_data)


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    time_assigned = (context.get_remaining_time_in_millis()
                     - MILLISECONDS_BEFORE_SPLIT)
    message = json.loads(event['Records'][0]['Sns']['Message'])
    location = message['location']
    region = message['region']
    slice_size_mbp = message['slice_size']
    summarise_slice(location, region, slice_size, time_assigned)
