import json
import os
import boto3
import time

from api_response import bundle_response


athena = boto3.client('athena')

BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']
METADATA_DATABASE = os.environ['METADATA_DATABASE']
INDIVIDUALS_TABLE = os.environ['INDIVIDUALS_TABLE']
ATHENA_WORKGROUP = os.environ['ATHENA_WORKGROUP']


def fetch_athena_data():
    response = athena.start_query_execution(
        QueryString='''
        select distinct cast(term as varchar) as term, cast(label as varchar), cast(type as varchar) from (
        select distinct json_extract(ethnicity, '$.id') as term, json_extract(ethnicity, '$.label') as label, 'string' as type from "sbeacon-metadata"."sbeacon-individuals"
        union
        select distinct json_extract(geographicorigin, '$.id') as term, json_extract(geographicorigin, '$.label') as label, 'string' as type from "sbeacon-metadata"."sbeacon-individuals"
        union
        select distinct json_extract(sex, '$.id') as term, json_extract(sex, '$.label') as label, 'string' as type from "sbeacon-metadata"."sbeacon-individuals"
        ) order by term asc;
        ''',
        # ClientRequestToken='string',
        QueryExecutionContext={
            'Database': 'sbeacon-metadata'
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
            filteringTerms = []
            for row in data['ResultSet']['Rows'][1:]:
                term, label, typ = row['Data']
                term, label, typ = term['VarCharValue'], label['VarCharValue'], typ['VarCharValue']
                filteringTerms.append({
                    "id": term,
                    "label": label,
                    "type": typ
                })
            return filteringTerms


def get_entry_types():
    response =     {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "info": {},
        "meta": {
            "apiVersion": BEACON_API_VERSION,
            "beaconId": BEACON_ID,
            "returnedSchemas": []
        },
        "response": {
            "filteringTerms": fetch_athena_data(),
            "resources": [
                {
                    "id": "NA",
                    "iriPrefix": "NA",
                    "name": "NA",
                    "namespacePrefix": "NA",
                    "url": "NA",
                    "version": "TBD"
                }
            ]
        }
    }

    return bundle_response(200, response)


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    response = get_entry_types()
    print('Returning Response: {}'.format(json.dumps(response)))
    return response


if __name__ == '__main__':
    lambda_handler({}, {})
