import gzip
import json
import os

import boto3
from botocore.exceptions import ClientError

from index_reader import Csi, Tbi

COUNTS = [
    'variantCount',
    'callCount',
    'sampleCount',
]

SUMMARISE_SLICE_SNS_TOPIC_ARN = os.environ['SUMMARISE_SLICE_SNS_TOPIC_ARN']
VARIANTS_BUCKET = os.environ['VARIANTS_BUCKET']
VCF_SUMMARIES_TABLE_NAME = os.environ['VCF_SUMMARIES_TABLE']

# Time/Cost estimation variables
MIN_SS_TIME = 0.1  # minimum time summariseSlice will run (s)
SS_RATE = 75000000  # Processing speed of summariseSlice (B/s)
SNS_TIME = 0.02  # Time to publish a message to SNS
MAX_CONCURRENCY = 1000  # Maximum number of summariseSlice functions to invoke


dynamodb = boto3.client('dynamodb')
s3 = boto3.client('s3')
sns = boto3.client('sns')


def delete_old_variant_files(location: str):
    contigs = get_contigs()
    objects = []
    for contig in contigs:
        # Remove leading "s3://" and trailing "vcf.gz" and change "/" delimiters
        key_prefix = f'vcf-summaries/contig/{contig}/' + location[5:-7].replace('/', '%') + '/'
        list_kwargs = {
            'Bucket': VARIANTS_BUCKET,
            'Prefix': key_prefix,
        }
        while True:
            print(f"Calling s3.list_objects_v2 with kwargs: {json.dumps(list_kwargs)}")
            list_response = s3.list_objects_v2(**list_kwargs)
            print(f"Received_response: {json.dumps(list_response, default=str)}")
            objects += [
                {'Key': obj['Key']}
                for obj in list_response.get('Contents', [])
            ]
            if list_response['IsTruncated']:
                list_kwargs['ContinuationToken'] = list_response['NextContinuationToken']
            else:
                break
    while objects:
        delete_kwargs = {
            'Bucket': VARIANTS_BUCKET,
            'Delete': {
                'Objects': objects[:1000],
                'Quiet': True,
            }
        }
        print(f"Calling s3.delete_objects with kwargs: {json.dumps(delete_kwargs)}")
        response = s3.delete_objects(**delete_kwargs)
        print(f"Received response {json.dumps(response, default=str)}")
        assert not response.get('Errors')
        objects = objects[1000:]


def find_best_split(total_size, epsilon):
    next_size = total_size ** 0.5
    sizes = []
    while True:
        sizes.append(next_size)
        # Use Newton's approximation to find next best split size
        next_size = next_newton_approximation(total_size, next_size)
        if next_size <= 0:
            # We've jumped over to the negative side, where the approximation diverges. try a smaller size.
            next_size = sizes[-1] / 2
        # Check if the sizes are converging
        if len(sizes) >= 2:
            last_difference = next_size - sizes[-1]
            rate = last_difference / (sizes[-1] - sizes[-2])
            if abs(rate) < 1:
                max_error = last_difference / (1 - rate)
                if abs(max_error) < epsilon:
                    break
    return next_size


def get_chunk_boundaries(location):
    index = get_vcf_index(location)
    bin_limit = index.bin_limit  # for excluding pseudobins
    return {
        ref_name: sorted(
            {
                chunk[chunk_delim]['virtual_file_offset']
                for bin in ref['bins']
                for chunk in bin['chunks']
                for chunk_delim in ('chunk_beg', 'chunk_end')
                if bin['bin'] < bin_limit
            }
        )
        for ref_name, ref in zip(index.names, index.refs)
    }


def get_contigs():
    """Get a list of all contigs for which variants are available."""
    contigs = []
    kwargs = {
        'Bucket': VARIANTS_BUCKET,
        'Delimiter': '/',
        'Prefix': f'vcf-summaries/contig/',
    }
    while True:
        resp = s3.list_objects_v2(**kwargs)
        contigs += [
            prefix['Prefix'].split('/')[-2]
            for prefix in resp.get('CommonPrefixes', [])
        ]
        if resp['IsTruncated']:
            kwargs['ContinuationToken'] = resp['NextContinuationToken']
        else:
            break
    return contigs


def get_sample_count(location, first_chunk_start):
    block_first_byte = first_chunk_start
    # We don't have the last byte, but we know blocks are no more than 64KB
    byterange = f'bytes=0-{block_first_byte+65335}'
    vcf_header = s3_get_object(location, Range=byterange)
    with gzip.GzipFile(mode='rb', fileobj=vcf_header) as header_stream:
        for line in header_stream:
            if not line.startswith(b'#'):
                print("VCF not formatted correctly, missing #CHROM\t...")
                raise ValueError("Incorrectly formatted file")
            elif line.startswith(b'#CHROM'):
                # Get the number of tabs after the FORMAT column
                return line.count(b'\t') - 8


def get_vcf_index(location, use_tbi=False):
    suffix = '.tbi' if use_tbi else '.csi'
    try:
        vcf_file = s3_get_object(location + suffix)
    except ClientError as error:
        if not use_tbi:
            print("Trying tbi index instead")
            return get_vcf_index(location, use_tbi=True)
        else:
            print("Could not access csi or tbi index, aborting")
            raise error
    else:
        return Tbi(vcf_file) if use_tbi else Csi(vcf_file)


def mark_updating(location, slices):
    slice_strings = [f'{start}-{end}' for start, end in slices]
    kwargs = {
        'TableName': VCF_SUMMARIES_TABLE_NAME,
        'Key': {
            'vcfLocation': {
                'S': location,
            },
        },
        'UpdateExpression': 'SET toUpdate=:toUpdate'
                            ' REMOVE ' + ', '.join(COUNTS),
        'ExpressionAttributeValues': {
            ':toUpdate': {
                'SS': slice_strings,
            },
        },
        'ConditionExpression': 'attribute_not_exists(toUpdate)',
    }
    print('Updating table: {}'.format(json.dumps(kwargs)))
    try:
        dynamodb.update_item(**kwargs)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            print("VCF location is already updating, aborting.")
            return False
        else:
            raise e
    return True


def next_newton_approximation(total_size, split_size):
    # Calculate derivatives for newton's approximation, so we don't need constant coefficients
    # Optimising for minimum total_time * cost
    d = -MIN_SS_TIME**2/split_size**2 + 1 / SS_RATE**2 - 2 * SNS_TIME * total_size * MIN_SS_TIME / split_size**3 - SNS_TIME * total_size / split_size**2 / SS_RATE
    dd = 2*MIN_SS_TIME**2/split_size**3 + 6 * SNS_TIME * total_size * MIN_SS_TIME / split_size**4 + 2 * SNS_TIME * total_size / split_size**3 / SS_RATE
    return split_size - d / dd


def partition_chunks(chunk_boundaries, slice_size):
    chunks = []
    for ref_chunk_boundaries in chunk_boundaries.values():
        start_virtual_offset = ref_chunk_boundaries[0]
        start_block_offset = start_virtual_offset >> 16
        for virtual_offset in ref_chunk_boundaries:
            if (virtual_offset >> 16) - start_block_offset >= slice_size:
                chunks.append((start_virtual_offset, virtual_offset))
                start_virtual_offset = virtual_offset
                start_block_offset = virtual_offset >> 16
        if ref_chunk_boundaries[-1] != start_virtual_offset:
            # We have a partially complete slice
            chunks.append((start_virtual_offset, ref_chunk_boundaries[-1]))
    return chunks


def publish_slice_updates(location, slices):
    kwargs = {
        'TopicArn': SUMMARISE_SLICE_SNS_TOPIC_ARN,
    }
    for virtual_start, virtual_end in slices:
        kwargs['Message'] = json.dumps({
            'location': location,
            'virtual_start': virtual_start,
            'virtual_end': virtual_end,
        })
        print('Publishing to SNS: {}'.format(json.dumps(kwargs)))
        response = sns.publish(**kwargs)
        print('Received Response: {}'.format(json.dumps(response)))


def s3_get_object(s3_location, **extra_kwargs):
    delim_index = s3_location.find('/', 5)
    bucket = s3_location[5:delim_index]
    key = s3_location[delim_index + 1:]
    kwargs = {
        'Bucket': bucket,
        'Key': key,
        **extra_kwargs
    }
    print(f"Calling s3.get_object with kwargs: {json.dumps(kwargs)}")
    try:
        response = s3.get_object(**kwargs)
    except ClientError as error:
        response = error.response
        print(f"Received error: {json.dumps(response, default=str)}")
        raise error
    else:
        print(f"Received response after: {json.dumps(response, default=str)}")
        return response['Body']


def summarise_vcf(location):
    chunk_boundaries = get_chunk_boundaries(location)
    first_chunk_start = min(boundaries[0] for boundaries in chunk_boundaries.values()) >> 16
    last_chunk_end = (max(boundaries[-1] for boundaries in chunk_boundaries.values()) >> 16) + 2**16
    num_chunks = sum(len(boundaries) for boundaries in chunk_boundaries.values()) - 1
    total_size = last_chunk_end - first_chunk_start
    print(f"{total_size=}")
    avg_chunk_size = total_size / num_chunks
    best_split_size = find_best_split(total_size, avg_chunk_size / 2)
    if total_size / best_split_size > MAX_CONCURRENCY:
        best_split_size = total_size / MAX_CONCURRENCY
    slices = partition_chunks(chunk_boundaries, best_split_size)
    start_update = mark_updating(location, slices)
    if not start_update:
        return
    sample_count = get_sample_count(location, first_chunk_start)
    update_sample_count(location, sample_count)
    delete_old_variant_files(location)
    publish_slice_updates(location, slices)


def update_sample_count(location, sample_count):
    kwargs = {
        'TableName': VCF_SUMMARIES_TABLE_NAME,
        'Key': {
            'vcfLocation': {
                'S': location,
            },
        },
        'UpdateExpression': 'SET sampleCount=:sampleCount',
        'ExpressionAttributeValues': {
            ':sampleCount': {
                'N': str(sample_count),
            },
        },
    }
    print('Updating table: {}'.format(json.dumps(kwargs)))
    dynamodb.update_item(**kwargs)


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    location = event['Records'][0]['Sns']['Message']
    summarise_vcf(location)
