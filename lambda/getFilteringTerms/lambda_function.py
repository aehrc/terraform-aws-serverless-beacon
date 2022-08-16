import json
import os
import pickle

from smart_open import open as sopen 

from apiutils.api_response import bundle_response


BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_ID = os.environ['BEACON_ID']
METADATA_BUCKET = os.environ['METADATA_BUCKET']


def get_entry_types(terms):
    response =     {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "info": {},
        "meta": {
            "apiVersion": BEACON_API_VERSION,
            "beaconId": BEACON_ID,
            "returnedSchemas": []
        },
        "response": {
            "filteringTerms": terms,
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
    with sopen(f's3://{METADATA_BUCKET}/indexes/filtering_terms.pkl', 'rb') as fi:
        data = pickle.load(fi)
    
        response = get_entry_types(
            sorted(
                [term for term in data],
                key=lambda term: term['id']
            )
        )
        print('Returning Response: {}'.format(json.dumps(response)))
        return response


if __name__ == '__main__':
    lambda_handler({}, {})
