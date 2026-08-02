import json
from concurrent.futures import ThreadPoolExecutor

import jsons

from shared.athena import Snp, entity_search_conditions
from shared.apiutils import (
    RequestParams,
    Granularity,
    DefaultSchemas,
    build_beacon_boolean_response,
    build_beacon_resultset_response,
    build_beacon_count_response,
    bundle_response,
)

# TODO create schema for SNPS and put it in default schemas

def get_count_query(conditions=""):
    query = f"""
    SELECT COUNT(id) FROM "{{database}}"."{{table}}"
    {conditions};
    """
    return query


def get_bool_query(conditions=""):
    query = f"""
    SELECT 1 FROM "{{database}}"."{{table}}"
    {conditions}
    LIMIT 1;
    """
    return query


def get_record_query(skip, limit, conditions=""):
    query = f"""
    SELECT * FROM "{{database}}"."{{table}}"
    {conditions}
    ORDER BY id
    OFFSET {skip}
    LIMIT {limit};
    """
    return query


def route(request: RequestParams):
    conditions, execution_parameters = entity_search_conditions(
        request.query.filters,
        "snps",
        "snps",
        request=request,
    )

    print(f"""Search condition summary:
        conditions: {conditions}
        params: {execution_parameters}
        """)

    if request.query.requested_granularity == Granularity.BOOLEAN:
        query = get_bool_query(conditions)
        count = (
            1
            if Snp.get_existence_by_query(
                query, execution_parameters=execution_parameters
            )
            else 0
        )
        response = build_beacon_boolean_response(
            {}, count, request, {}, DefaultSchemas.SAMPLES
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == Granularity.COUNT:
        query = get_count_query(conditions)
        count = Snp.get_count_by_query(
            query, execution_parameters=execution_parameters
        )
        response = build_beacon_count_response(
            {}, count, request, {}, DefaultSchemas.SAMPLES
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == Granularity.RECORD:
        executor = ThreadPoolExecutor(2)
        # records fetching
        record_query = get_record_query(
            request.query.pagination.skip, request.query.pagination.limit, conditions
        )
        record_future = executor.submit(
            Snp.get_by_query,
            record_query,
            execution_parameters=execution_parameters,
        )
        # counts fetching
        count_query = get_count_query(conditions)
        count_future = executor.submit(
            Snp.get_count_by_query,
            count_query,
            execution_parameters=execution_parameters,
        )
        executor.shutdown()
        count = count_future.result()
        data = record_future.result()
        print(f"Received record data: {data}")

        # Extract data from Athena record structure
        keys = [row["VarCharValue"] for row in data[0]["Data"]]
        final_data = []

        for row in data[1:]:
            vals = [col["VarCharValue"] for col in row["Data"]]
            final_data.append(dict(zip(keys, vals)))
        
        response = build_beacon_resultset_response(
            jsons.dump(final_data, strip_privates=True),
            count,
            request,
            {},
            DefaultSchemas.SAMPLES,
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return bundle_response(200, response)


if __name__ == "__main__":
    pass
