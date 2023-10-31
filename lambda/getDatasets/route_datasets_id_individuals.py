import json
from concurrent.futures import ThreadPoolExecutor

import jsons

from shared.athena import Individual, entity_search_conditions
from shared.apiutils import (
    RequestParams,
    Granularity,
    DefaultSchemas,
    build_beacon_boolean_response,
    build_beacon_resultset_response,
    build_beacon_count_response,
    bundle_response,
)


# TODO dataset and individual connection should be refactored
# confirmt hat, dataset and individual relate via 1..n
# what if same individual get two datasets? of would that just be 2 biosamples?
def get_bool_query(id, conditions=""):
    query = f"""
    SELECT 1 FROM "{{database}}"."{{table}}"
    WHERE "_datasetid"='{id}'
    {('AND ' + conditions) if len(conditions) > 0 else ''}
    LIMIT 1;
    """

    return query


def get_count_query(id, conditions=""):
    query = f"""
    SELECT COUNT(*) FROM "{{database}}"."{{table}}"
    WHERE "_datasetid"='{id}'
    {('AND ' + conditions) if len(conditions) > 0 else ''}
    """

    return query


def get_record_query(id, skip, limit, conditions=""):
    query = f"""
    SELECT * FROM "{{database}}"."{{table}}"
    WHERE "_datasetid"='{id}'
    {('AND ' + conditions) if len(conditions) > 0 else ''}
    ORDER BY id
    OFFSET {skip}
    LIMIT {limit};
    """

    return query


def route(request: RequestParams, dataset_id):
    conditions, execution_parameters = entity_search_conditions(
        request.query.filters, "individuals", "individuals", with_where=False
    )

    if request.query.requested_granularity == "boolean":
        query = get_bool_query(dataset_id, conditions)
        count = (
            1
            if Individual.get_existence_by_query(
                query, execution_parameters=execution_parameters
            )
            else 0
        )
        response = build_beacon_boolean_response(
            {}, count, request, {}, DefaultSchemas.INDIVIDUALS
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == "count":
        query = get_count_query(dataset_id, conditions)
        count = Individual.get_count_by_query(
            query, execution_parameters=execution_parameters
        )
        response = build_beacon_count_response(
            {}, count, request, {}, DefaultSchemas.INDIVIDUALS
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == Granularity.RECORD:
        executor = ThreadPoolExecutor(2)
        # records fetching
        record_query = get_record_query(
            dataset_id,
            request.query.pagination.skip,
            request.query.pagination.limit,
            conditions,
        )
        record_future = executor.submit(
            Individual.get_by_query,
            record_query,
            execution_parameters=execution_parameters,
        )
        # counts fetching
        count_query = get_count_query(dataset_id, conditions)
        count_future = executor.submit(
            Individual.get_count_by_query,
            count_query,
            execution_parameters=execution_parameters,
        )
        executor.shutdown()
        count = count_future.result()
        individuals = record_future.result()
        response = build_beacon_resultset_response(
            jsons.dump(individuals, strip_privates=True),
            count,
            request,
            {},
            DefaultSchemas.INDIVIDUALS,
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return bundle_response(200, response)
