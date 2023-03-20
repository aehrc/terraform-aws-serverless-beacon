import json

import jsons

from shared.athena import Run
from shared.apiutils import (
    DefaultSchemas,
    RequestParams,
    Granularity,
    build_beacon_boolean_response,
    build_beacon_resultset_response,
    build_beacon_count_response,
    bundle_response,
)


def get_record_query(id):
    query = f"""
    SELECT * FROM "{{database}}"."{{table}}"
    WHERE "id"='{id}'
    LIMIT 1;
    """

    return query


def route(request: RequestParams, run_id):
    if request.query.requested_granularity == "boolean":
        query = get_record_query(run_id)
        count = 1 if Run.get_existence_by_query(query) else 0
        response = build_beacon_boolean_response(
            {}, count, request, {}, DefaultSchemas.RUNS
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == "count":
        query = get_record_query(run_id)
        count = 1 if Run.get_existence_by_query(query) else 0
        response = build_beacon_count_response(
            {}, count, request, {}, DefaultSchemas.RUNS
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == Granularity.RECORD:
        query = get_record_query(run_id)
        runs = Run.get_by_query(query)
        response = build_beacon_resultset_response(
            jsons.dump(runs, strip_privates=True),
            len(runs),
            request,
            {},
            DefaultSchemas.RUNS,
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return bundle_response(200, response)
