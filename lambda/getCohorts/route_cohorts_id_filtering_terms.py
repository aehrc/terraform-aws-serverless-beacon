import json
import os
import csv

from smart_open import open as sopen

from apiutils.responses import build_filtering_terms_response, bundle_response
from athena.common import run_custom_query
from apiutils.requests import RequestParams


ATHENA_TERMS_TABLE = os.environ['ATHENA_TERMS_TABLE']
ATHENA_METADATA_BUCKET = os.environ['ATHENA_METADATA_BUCKET']
ATHENA_TERMS_INDEX_TABLE = os.environ['ATHENA_TERMS_INDEX_TABLE']
ATHENA_INDIVIDUALS_TABLE = os.environ['ATHENA_INDIVIDUALS_TABLE']
ATHENA_BIOSAMPLES_TABLE = os.environ['ATHENA_BIOSAMPLES_TABLE']
ATHENA_RUNS_TABLE = os.environ['ATHENA_RUNS_TABLE']
ATHENA_ANALYSES_TABLE = os.environ['ATHENA_ANALYSES_TABLE']


def route(request: RequestParams, cohort_id):
    query = f'''
        SELECT DISTINCT term, label, type 
        FROM "{ATHENA_TERMS_TABLE}"
        WHERE term IN
        (
            SELECT DISTINCT TI.term
            FROM "{ATHENA_TERMS_INDEX_TABLE}" TI
            WHERE TI.id = '{cohort_id}' and TI.kind = 'cohorts'

            UNION

            SELECT DISTINCT TI.term
            FROM "{ATHENA_INDIVIDUALS_TABLE}" I
            JOIN 
            "{ATHENA_TERMS_INDEX_TABLE}" TI
            ON TI.id = I.id and TI.kind = 'individuals'
            WHERE I._cohortid = '{cohort_id}'

            UNION

            SELECT DISTINCT TI.term
            FROM "{ATHENA_BIOSAMPLES_TABLE}" B
            JOIN 
            "{ATHENA_TERMS_INDEX_TABLE}" TI
            ON TI.id = B.id and TI.kind = 'biosamples'
            WHERE B._cohortid = '{cohort_id}'

            UNION

            SELECT DISTINCT TI.term
            FROM "{ATHENA_RUNS_TABLE}" R
            JOIN 
            "{ATHENA_TERMS_INDEX_TABLE}" TI
            ON TI.id = R.id and TI.kind = 'runs'
            WHERE R._cohortid = '{cohort_id}'

            UNION

            SELECT DISTINCT TI.term
            FROM "{ATHENA_ANALYSES_TABLE}" A
            JOIN 
            "{ATHENA_TERMS_INDEX_TABLE}" TI
            ON TI.id = A.id and TI.kind = 'analyses'
            WHERE A._cohortid = '{cohort_id}'
        )
        ORDER BY term
        OFFSET {request.query.pagination.skip}
        LIMIT {request.query.pagination.limit};
    '''

    exec_id = run_custom_query(query, return_id=True)
    filteringTerms = []

    with sopen(f's3://{ATHENA_METADATA_BUCKET}/query-results/{exec_id}.csv') as s3f:
        reader = csv.reader(s3f)

        for n, row in enumerate(reader):
            if n == 0:
                continue
            term, label, typ = row
            filteringTerms.append({
                "id": term,
                "label": label,
                "type": typ
            })

    response = build_filtering_terms_response(
        filteringTerms,
        [],
        request
    )

    print('Returning Response: {}'.format(json.dumps(response)))
    return bundle_response(200, response)
