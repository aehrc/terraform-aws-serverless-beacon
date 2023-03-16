import json
import os

import jsons

import apiutils.responses as responses
from athena.cohort import Cohort
from apiutils.schemas import DefaultSchemas
from apiutils.requests import RequestParams, Granularity


ATHENA_INDIVIDUALS_TABLE = os.environ["ATHENA_INDIVIDUALS_TABLE"]


def get_record_query(id):
    query = f"""
    SELECT id, cohortdatatypes, cohortdesign, COALESCE(B.csize, 0) as cohortsize, cohorttype, collectionevents, exclusioncriteria, inclusioncriteria, name
    FROM 
        (
            SELECT * FROM "{{database}}"."{{table}}"
            WHERE id='{id}'
        ) as A 
    LEFT JOIN 
        (
            SELECT _cohortid, count(*) as csize 
            FROM "{{database}}"."{ATHENA_INDIVIDUALS_TABLE}"
            WHERE _cohortid='{id}'
            GROUP BY _cohortid
        ) as B
    ON A.id = B._cohortid
    LIMIT 1;
    """

    return query


def route(request: RequestParams, cohort_id):
    if request.query.requested_granularity == Granularity.BOOLEAN:
        query = get_record_query(cohort_id)
        count = 1 if Cohort.get_existence_by_query(query) else 0
        response = responses.build_beacon_boolean_response(
            {}, count, request, {}, DefaultSchemas.COHORTS
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return responses.bundle_response(200, response)

    if request.query.requested_granularity == Granularity.COUNT:
        query = get_record_query(cohort_id)
        count = 1 if Cohort.get_existence_by_query(query) else 0
        response = responses.build_beacon_count_response(
            {}, count, request, {}, DefaultSchemas.COHORTS
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return responses.bundle_response(200, response)

    if request.query.requested_granularity == Granularity.RECORD:
        query = get_record_query(cohort_id)
        cohorts = Cohort.get_by_query(query)
        response = responses.build_beacon_collection_response(
            jsons.dump(cohorts, strip_privates=True),
            len(cohorts),
            request,
            lambda x, y: x,
            DefaultSchemas.COHORTS,
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return responses.bundle_response(200, response)
