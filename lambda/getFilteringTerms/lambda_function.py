import csv
import json

from smart_open import open as sopen

from shared.athena import run_custom_query
from shared.dynamodb import Ontology
from shared.utils import ENV_ATHENA
from shared.apiutils import (
    build_filtering_terms_response,
    parse_request,
    bundle_response,
)


def lambda_handler(event, context):
    print("event received", event)
    request, errors, status = parse_request(event)

    if errors:
        return bundle_response(status, errors)

    query = f"""
    SELECT DISTINCT term, label, type 
    FROM "{ENV_ATHENA.ATHENA_TERMS_TABLE}"
    OFFSET {request.query.pagination.skip}
    LIMIT {request.query.pagination.limit};
    """

    exec_id = run_custom_query(query, return_id=True)
    filteringTerms = []
    ontologies = set()

    with sopen(
        f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/query-results/{exec_id}.csv"
    ) as s3f:
        reader = csv.reader(s3f)

        for n, row in enumerate(reader):
            if n == 0:
                continue
            term, label, typ = row
            ontologies.add(term.split(":")[0].lower())
            filteringTerms.append({"id": term, "label": label, "type": typ})

    resources = [
        ontology.attribute_values for ontology in Ontology.batch_get(ontologies)
    ]
    response = build_filtering_terms_response(filteringTerms, resources, request)

    print("Returning Response: {}".format(json.dumps(response)))
    return bundle_response(200, response)


if __name__ == "__main__":
    pass
