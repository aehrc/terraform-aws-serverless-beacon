import json
import jsons

import shared.apiutils.responses as responses
from shared.athena.analysis import Analysis
from shared.apiutils.schemas import DefaultSchemas
from shared.apiutils.requests import RequestParams, Granularity


def get_record_query(id):
    query = f"""
    SELECT * FROM "{{database}}"."{{table}}"
    WHERE "id"='{id}'
    LIMIT 1;
    """
    return query


def route(request: RequestParams, analysis_id):
    if request.query.requested_granularity == Granularity.BOOLEAN:
        query = get_record_query(analysis_id)
        count = 1 if Analysis.get_existence_by_query(query) else 0
        response = responses.build_beacon_boolean_response(
            {}, count, request, {}, DefaultSchemas.ANALYSES
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return responses.bundle_response(200, response)

    if request.query.requested_granularity == Granularity.COUNT:
        query = get_record_query(analysis_id)
        count = 1 if Analysis.get_existence_by_query(query) else 0
        response = responses.build_beacon_count_response(
            {}, count, request, {}, DefaultSchemas.ANALYSES
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return responses.bundle_response(200, response)

    if request.query.requested_granularity == Granularity.RECORD:
        query = get_record_query(analysis_id)
        analyses = Analysis.get_by_query(query)
        response = responses.build_beacon_resultset_response(
            jsons.dump(analyses, strip_privates=True),
            len(analyses),
            request,
            {},
            DefaultSchemas.ANALYSES,
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return responses.bundle_response(200, response)
