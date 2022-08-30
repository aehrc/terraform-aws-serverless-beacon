import json
import os

from athena.common import run_custom_query
from apiutils.api_response import bad_request, bundle_response


BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']
TERMS_TABLE = os.environ['TERMS_TABLE']


def get_terms(terms, skip, limit):
    response =     {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "info": {},
        "meta": {
            "apiVersion": BEACON_API_VERSION,
            "beaconId": BEACON_ID,
            "returnedSchemas": [],
            "receivedRequestSummary": {
                "apiVersion": "get from request",  # TODO
                "requestedSchemas": [],  # TODO
                "pagination": {
                    "skip": skip,
                    "limit": limit,
                },
                "requestedGranularity": "record"  # TODO
            }
        },
        "response": {
            "filteringTerms": terms,
            # "resources": [
            #     {
            #         "id": "NA",
            #         "iriPrefix": "NA",
            #         "name": "NA",
            #         "namespacePrefix": "NA",
            #         "url": "NA",
            #         "version": "TBD"
            #     }
            # ]
        }
    }

    return bundle_response(200, response)


def lambda_handler(event, context):
    print('event received', event)
    if (event['httpMethod'] == 'GET'):
        params = event['queryStringParameters'] or dict()
        skip = params.get("skip", 0)
        limit = params.get("limit", 100)
    else:
        return bad_request(apiVersion=BEACON_API_VERSION, errorMessage='Only GET requests are serverd')
    
    query = f'''
    SELECT DISTINCT term, label, type 
    FROM "{TERMS_TABLE}"
    OFFSET {skip}
    LIMIT {limit};
    '''

    print('Performing query \n', query)
        
    rows = run_custom_query(query)
    filteringTerms = []
    for row in rows:
        term, label, typ = row['Data']
        term, label, typ = term['VarCharValue'], label.get('VarCharValue'), typ.get('VarCharValue')
        filteringTerms.append({
            "id": term,
            "label": label,
            "type": typ
        })

    response = get_terms(
        sorted(filteringTerms, key=lambda x: x['id']),
        skip=skip,
        limit=limit
    )
    print('Returning Response: {}'.format(json.dumps(response)))
    return response


if __name__ == '__main__':
    pass
