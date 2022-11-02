import json
import os
import concurrent.futures

import boto3
import jsons

from payloads.lambda_payloads import SplitQueryPayload, PerformQueryPayload


SPLIT_SIZE = 10000
PERFORM_QUERY = os.environ['PERFORM_QUERY_LAMBDA']
PERFORM_QUERY_TOPIC_ARN = os.environ['PERFORM_QUERY_TOPIC_ARN']

aws_lambda = boto3.client('lambda')
sns = boto3.client('sns')


def perform_query(payload):
    # response = aws_lambda.invoke(
    #     FunctionName=PERFORM_QUERY,
    #     InvocationType='Event',
    #     Payload=jsons.dumps(payload),
    # )
    kwargs = {
        'TopicArn': PERFORM_QUERY_TOPIC_ARN,
        'Message': jsons.dumps(payload)
    }
    sns.publish(**kwargs)


def split_query(split_payload: SplitQueryPayload):
    # to find HITs or ALL we must analyse all vcfs
    check_all = split_payload.include_datasets in ('HIT', 'ALL')

    split_start = split_payload.start_min
    pool = concurrent.futures.ThreadPoolExecutor(32)

    while split_start <= split_payload.start_max:
        split_end = min(split_start + SPLIT_SIZE - 1, split_payload.start_max)
        # perform query on this split of the vcf
        for vcf_location, chrom in split_payload.vcf_locations.items():
            payload = PerformQueryPayload(
                passthrough=split_payload.passthrough,
                dataset_id=split_payload.dataset_id,
                query_id=split_payload.query_id,
                reference_bases=split_payload.reference_bases,
                end_min=split_payload.end_min,
                end_max=split_payload.end_max,
                alternate_bases=split_payload.alternate_bases,
                variant_type=split_payload.variant_type,
                requested_granularity=split_payload.requested_granularity,
                variant_min_length=split_payload.variant_min_length,
                variant_max_length=split_payload.variant_max_length,
                include_details=check_all,
                # region for bcftools
                region=f'{chrom}:{split_start}-{split_end}',
                vcf_location=vcf_location
            )
            pool.submit(perform_query, payload)

        # next split
        split_start += SPLIT_SIZE

    pool.shutdown()


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    
    try:
        event = json.loads(event['Records'][0]['Sns']['Message'])
        print('using sns event')
    except:
        print('using invoke event')

    split_payload = jsons.load(event, SplitQueryPayload)

    print(split_payload)
    response = split_query(split_payload)
    print('Completed split query')

    return response


if __name__ == '__main__':
    event = {
    "Records": [
            {
                "EventSource": "aws:sns",
                "EventVersion": "1.0",
                "EventSubscriptionArn": "arn:aws:sns:us-east-1:361439923243:splitQuery:abe5cdb5-03bd-4363-9bd3-b3fd9ee2c881",
                "Sns": {
                    "Type": "Notification",
                    "MessageId": "46ba922a-cc5e-50a7-855f-c9f3e5d7c198",
                    "TopicArn": "arn:aws:sns:us-east-1:361439923243:splitQuery",
                    "Subject": None,
                    "Message": "{\"payload\": {\"alternate_bases\": \"N\", \"dataset_id\": \"3-385\", \"end_max\": 10000011, \"end_min\": 10000001, \"include_datasets\": \"HIT\", \"passthrough\": {}, \"query_id\": \"01b802e52199e6c0143e0e93088d8578\", \"reference_bases\": \"A\", \"requested_granularity\": \"record\", \"start_max\": 10000011, \"start_min\": 10000001, \"variant_max_length\": -1, \"variant_min_length\": 0, \"variant_type\": null, \"vcf_groups\": [], \"vcf_locations\": {\"s3://sample-vcfs/100160.notY.vcf.gz\": \"5\"}}}",
                    "Timestamp": "2022-10-31T01:39:21.419Z",
                    "SignatureVersion": "1",
                    "Signature": "B/KhtR5klnl3O5gMoGYQFIOcRi+RcTgzlDIB8TCA+S7hcmSwDkmUrJXdemrjQnqL7W19amTX4ISKtQ22suCNa2BZvXIyx5WiuRbE6j+/ggXZteibWmEVCIhmrtn2zguijrW/0YSQabX31Ki9FARoSxtrdxvJ3wq4alMaU0hne1uVat7FHgEyiTx98gAgCL6OOpXvSgijTNBNBSIK6iKeUPhZtvPUaOru9zwSJsY9MVBYtW0RPd6OsfkgKM79Fb0f3B7JBItqJzBtAke0KqZ5t41a4io1h61r9kbx4XxluyVjc1KQQQVWDPeKGrh/uAPk5u9e9tnWAR1Oz2ePOoZ7gw==",
                    "SigningCertUrl": "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-56e67fcb41f6fec09b0196692625d385.pem",
                    "UnsubscribeUrl": "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:361439923243:splitQuery:abe5cdb5-03bd-4363-9bd3-b3fd9ee2c881",
                    "MessageAttributes": {}
                }
            }
        ]
    }

    lambda_handler(event, dict())
