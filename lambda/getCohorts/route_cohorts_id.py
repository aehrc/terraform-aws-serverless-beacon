import json

import jsons

from shared.athena import Cohort
from shared.utils import ENV_ATHENA
from shared.apiutils import (
    RequestParams,
    Granularity,
    DefaultSchemas,
    build_beacon_boolean_response,
    build_beacon_collection_response,
    build_beacon_count_response,
    bundle_response,
)


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
            FROM "{{database}}"."{ENV_ATHENA.ATHENA_INDIVIDUALS_TABLE}"
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
        response = build_beacon_boolean_response(
            {}, count, request, {}, DefaultSchemas.COHORTS
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == Granularity.COUNT:
        query = get_record_query(cohort_id)
        count = 1 if Cohort.get_existence_by_query(query) else 0
        response = build_beacon_count_response(
            {}, count, request, {}, DefaultSchemas.COHORTS
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == Granularity.RECORD:
        query = get_record_query(cohort_id)
        cohorts = Cohort.get_by_query(query)
        response = build_beacon_collection_response(
            jsons.dump(cohorts, strip_privates=True),
            len(cohorts),
            request,
            lambda x, y: x,
            DefaultSchemas.COHORTS,
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return bundle_response(200, response)
