import json
from concurrent.futures import ThreadPoolExecutor

import jsons

from shared.athena import entity_search_conditions
from shared.apiutils.requests import RequestParams, Granularity
from shared.apiutils import DefaultSchemas
import shared.apiutils.responses as responses
from shared.athena.cohort import Cohort
from shared.utils import ENV_ATHENA


def get_count_query(conditions=[]):
    query = f"""
    SELECT COUNT(id) FROM "{{database}}"."{{table}}"
    {conditions};
    """
    return query


def get_bool_query(conditions=[]):
    query = f"""
    SELECT 1 FROM "{{database}}"."{{table}}" 
    {conditions}
    LIMIT 1;
    """
    return query


def get_record_query(skip, limit, conditions=[]):
    # TODO cohorts and individuals must be related via a many-to-many table
    query = f"""
    SELECT id, cohortdatatypes, cohortdesign, cohortsize, cohorttype, collectionevents, exclusioncriteria, inclusioncriteria, name
    FROM "{{database}}"."{{table}}"
    {conditions}
    ORDER BY id
    OFFSET {skip}
    LIMIT {limit};
    """
    return query


def route(request: RequestParams):
    conditions, execution_parameters = entity_search_conditions(
        request.query.filters, "cohorts", "cohorts"
    )

    if request.query.requested_granularity == Granularity.BOOLEAN:
        query = get_bool_query(conditions)
        count = (
            1
            if Cohort.get_existence_by_query(
                query, execution_parameters=execution_parameters
            )
            else 0
        )
        response = responses.build_beacon_boolean_response(
            {}, count, request, {}, DefaultSchemas.COHORTS
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return responses.bundle_response(200, response)

    if request.query.requested_granularity == Granularity.COUNT:
        query = get_count_query(conditions)
        count = Cohort.get_count_by_query(
            query, execution_parameters=execution_parameters
        )
        response = responses.build_beacon_count_response(
            {}, count, request, {}, DefaultSchemas.COHORTS
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return responses.bundle_response(200, response)

    if request.query.requested_granularity == Granularity.RECORD:
        executor = ThreadPoolExecutor(2)
        # records fetching
        record_query = get_record_query(
            request.query.pagination.skip, request.query.pagination.limit, conditions
        )
        record_future = executor.submit(
            Cohort.get_by_query, record_query, execution_parameters=execution_parameters
        )
        # counts fetching
        count_query = get_count_query(conditions)
        count_future = executor.submit(
            Cohort.get_count_by_query,
            count_query,
            execution_parameters=execution_parameters,
        )
        executor.shutdown()
        count = count_future.result()
        cohorts = record_future.result()
        response = responses.build_beacon_collection_response(
            jsons.dump(cohorts, strip_privates=True),
            count,
            request,
            lambda x, y: x,
            DefaultSchemas.COHORTS,
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return responses.bundle_response(200, response)


if __name__ == "__main__":
    pass
