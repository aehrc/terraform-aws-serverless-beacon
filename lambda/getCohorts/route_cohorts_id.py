import json
import os
import jsons

import boto3

from apiutils.api_response import bundle_response
import apiutils.responses as responses
from athena.cohort import Cohort


BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']
INDIVIDUALS_TABLE = os.environ['INDIVIDUALS_TABLE']

s3 = boto3.client('s3')


def get_record_query(id):
    query = f'''
    SELECT id, cohortdatatypes, cohortdesign, B.csize as cohortsize, cohorttype, collectionevents, exclusioncriteria, inclusioncriteria, name
    FROM 
        (
            SELECT * FROM "{{database}}"."{{table}}"
            WHERE id='{id}'
        ) as A 
    JOIN 
        (
            SELECT _cohortid, count(*) as csize 
            FROM "{{database}}"."{INDIVIDUALS_TABLE}"
            WHERE _cohortid='{id}'
            GROUP BY _cohortid
        ) as B
    ON A.id = B._cohortid
    LIMIT 1;
    '''

    return query


def route(event):
    if event['httpMethod'] == 'GET':
        params = event.get('queryStringParameters', None) or dict()
        print(f"Query params {params}")
        apiVersion = params.get("apiVersion", BEACON_API_VERSION)
        requestedSchemas = params.get("requestedSchemas", [])
        requestedGranularity = params.get("requestedGranularity", "boolean")

    if event['httpMethod'] == 'POST':
        params = json.loads(event.get('body') or "{}")
        print(f"POST params {params}")
        meta = params.get("meta", dict())
        query = params.get("query", dict())
        # meta data
        apiVersion = meta.get("apiVersion", BEACON_API_VERSION)
        requestedSchemas = meta.get("requestedSchemas", [])
        # query data
        requestedGranularity = query.get("requestedGranularity", "boolean")
        # query request params
        requestParameters = query.get("requestParameters", dict())
    
    cohort_id = event["pathParameters"].get("id", None)
    
    if request.query.requested_granularity =='boolean':
        query = get_record_query(cohort_id)
        exists = Cohort.get_existence_by_query(query)
        response = responses.get_boolean_response(exists=exists)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity =='count':
        query = get_record_query(cohort_id)
        count = Cohort.get_count_by_query(query)
        response = responses.get_counts_response(exists=count>0, count=count)
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == Granularity.RECORD:
        query = get_record_query(cohort_id)
        cohorts = Cohort.get_by_query(query)
        response = responses.get_result_sets_response(
            setType='cohorts', 
            exists=len(cohorts)>0,
            total=len(cohorts),
            results=jsons.dump(cohorts, strip_privates=True)
        )
        print('Returning Response: {}'.format(json.dumps(response)))
        return bundle_response(200, response)
