import json
import csv

from smart_open import open as sopen

from shared.apiutils import RequestParams, build_filtering_terms_response, bundle_response
from shared.athena import run_custom_query
from shared.utils import ENV_ATHENA


def route(request: RequestParams):
    query = f"""
    SELECT DISTINCT term, label, type 
    FROM "{ENV_ATHENA.ATHENA_TERMS_TABLE}"
    WHERE "kind"='analyses'
    ORDER BY term
    OFFSET {request.query.pagination.skip}
    LIMIT {request.query.pagination.limit};
    """

    exec_id = run_custom_query(query, return_id=True)
    filteringTerms = []

    with sopen(
        f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/query-results/{exec_id}.csv"
    ) as s3f:
        reader = csv.reader(s3f)

        for n, row in enumerate(reader):
            if n == 0:
                continue
            term, label, typ = row
            filteringTerms.append({"id": term, "label": label, "type": typ})

    response = build_filtering_terms_response(filteringTerms, [], request)

    print("Returning Response: {}".format(json.dumps(response)))
    return bundle_response(200, response)
