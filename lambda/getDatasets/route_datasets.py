import json

import jsons

from shared.athena import Dataset, entity_search_conditions
from shared.apiutils import (
    RequestParams,
    Granularity,
    DefaultSchemas,
    build_beacon_boolean_response,
    build_beacon_collection_response,
    build_beacon_count_response,
    bundle_response,
)


# TODO Datasets must only hold VCFs, they must not be related to anything else
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
        request.query.filters, "datasets", "datasets"
    )

    if request.query.requested_granularity == "boolean":
        query = get_bool_query(conditions)
        count = (
            1
            if Dataset.get_existence_by_query(
                query, execution_parameters=execution_parameters
            )
            else 0
        )
        response = build_beacon_boolean_response(
            {}, count, request, {}, DefaultSchemas.DATASETS
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == "count":
        query = get_count_query(conditions)
        count = Dataset.get_count_by_query(
            query, execution_parameters=execution_parameters
        )
        response = build_beacon_count_response(
            {}, count, request, {}, DefaultSchemas.DATASETS
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return bundle_response(200, response)

    if request.query.requested_granularity == Granularity.RECORD:
        query = get_record_query(
            request.query.pagination.skip, request.query.pagination.limit, conditions
        )
        datasets = Dataset.get_by_query(
            query, execution_parameters=execution_parameters
        )
        response = build_beacon_collection_response(
            jsons.dump(datasets, strip_privates=True),
            len(datasets),
            request,
            lambda x, y: x,
            DefaultSchemas.DATASETS,
        )
        print("Returning Response: {}".format(json.dumps(response)))
        return bundle_response(200, response)


if __name__ == "__main__":
    pass
