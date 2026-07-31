import json
from copy import deepcopy
from typing import Dict

from shared.apiutils.router import LambdaRouter
from utils import templates
from utils.auth import authenticate_endpoint
from utils.db import search_db
from utils.models import (
    Aggregation,
    AggregationEnum,
    Filters,
    FilterTypeEnum,
    Granularity,
    GranularityEnum,
    Region,
    Scope,
    SheepScopeEnum,
)

router = LambdaRouter()


def _empty_response(message):
    return {
        "success": False,
        "response_text": message,
        "history": dict(),
        "response_data": None,
    }


@router.attach("/ask/query", "post", authenticate_endpoint)
def query(event, context):
    # json.loads(None) raises TypeError, which surfaced as a 502 rather than a
    # useful message whenever the body was missing.
    raw_body = event.get("body") or "{}"
    try:
        body_dict = json.loads(raw_body)
    except ValueError:
        return _empty_response("Could not read the request body. Expected JSON.")

    user_query = body_dict.get("query", None)
    history = body_dict.get("history", dict()) or dict()

    if not user_query:
        return _empty_response("Please submit your query again.")

    # ---------------------------------------------------------------- validate
    validate_and_followup_chain = templates.get_validate_and_followup_chain()
    payload = {
        "history": "\n".join(f"{k}: {v}" for k, v in history.items()),
        "query": user_query,
    }
    print(f"Invoke 'validate_and_followup_chain' {payload=}")
    response = validate_and_followup_chain.invoke(payload)

    if not response["valid"]:
        print(f"Validation failed: {user_query=} {response=}")
        return {
            "success": False,
            "response_text": response["response"],
            "response_data": None,
            "history": dict(),
        }
    print(f"Validation success: {user_query=}")

    # ----------------------------------------------------------------- extract
    extractor_chain = templates.get_data_extractor_map_chain()
    print(f"Invoke 'extractor_chain' {user_query=}")
    result: Dict[str, Scope | Filters | Granularity | Region | Aggregation] = (
        extractor_chain.invoke(user_query)
    )

    extracted_data = dict()
    unresolved = []
    ontology_hits = []
    next_history = deepcopy(history)

    # scope ---------------------------------------------------------------- #
    scope = result["scope"]
    if scope.scope != SheepScopeEnum.UNKNOWN:
        extracted_data["scope"] = scope.scope.value
        next_history["scope"] = extracted_data["scope"]

    # filters -------------------------------------------------------------- #
    # Structured (alphanumeric) filters go straight through as Beacon filters.
    # Only genuine ontology filters hit the vector search - previously every
    # condition, including numeric ones, was sent to search_db, which cannot
    # represent "> 4" and returned unrelated ontology terms.
    filters_out = []
    for fil in result["filters"].filters:
        if not fil.is_resolvable():
            unresolved.append(fil.field or fil.term or fil.value)
            continue

        if fil.type == FilterTypeEnum.ONTOLOGY:
            term = fil.term or fil.value
            for entry, score in search_db(term):
                hit = {
                    "type": "ontology",
                    "scope": fil.scope.value,
                    "term": entry.term,
                    "label": entry.label,
                    "score": score,
                    "query": term,
                }
                filters_out.append(hit)
                ontology_hits.append(hit)
        else:
            filters_out.append(
                {
                    "type": "alphanumeric",
                    "scope": fil.scope.value,
                    "field": fil.resolved_field,
                    "operator": fil.operator.value,
                    "value": fil.value,
                    "query": fil.describe(),
                }
            )

    if filters_out:
        extracted_data["filters"] = filters_out
        next_history["filters"] = "; ".join(
            f["query"] for f in filters_out if f.get("query")
        )

    if unresolved:
        extracted_data["unresolved_filters"] = unresolved

    # region --------------------------------------------------------------- #
    region: Region = result["region"]
    if region.success:
        start, end = region.as_bounds()
        region_data = {
            k: v
            for k, v in {
                "chromosome": region.chromosome,
                "start": start,
                "end": end,
                "snp_ids": region.snp_ids or None,
            }.items()
            if v not in (None, "unknown", [])
        }
        if region_data:
            extracted_data["region"] = region_data
            next_history["region"] = json.dumps(region_data)

    # granularity ----------------------------------------------------------- #
    granularity = result["granularity"]
    if granularity.granularity != GranularityEnum.UNKNOWN:
        extracted_data["granularity"] = granularity.granularity.value
        next_history["granularity"] = extracted_data["granularity"]

    # aggregation ----------------------------------------------------------- #
    aggregation = result["aggregation"]
    if aggregation.aggregation != AggregationEnum.NONE:
        extracted_data["aggregation"] = {
            "aggregation": aggregation.aggregation.value,
            "group_by": aggregation.group_by,
        }
        next_history["aggregation"] = aggregation.aggregation.value

    # ---------------------------------------------------------------- respond
    success_followup_chain = templates.get_success_followup_chain()
    payload = {
        "query": user_query,
        "extracted": "\n".join(f"{k}: {v}" for k, v in next_history.items()),
        "unresolved": ", ".join(unresolved),
        "terms": "\n".join(f"{hit['term']} - {hit['label']}" for hit in ontology_hits),
    }
    print(f"Invoke 'success_followup_chain' {payload=}")
    response_message = success_followup_chain.invoke(payload)
    response_text = getattr(response_message, "content", str(response_message))

    return {
        "response_data": extracted_data,
        "response_text": response_text,
        "history": next_history,
        "success": True,
    }


if __name__ == "__main__":
    for demo in (
        "What are the major and minor alleles for all SNPs between position 1 and 50,000 on chromosome 1?",
        "What are the allele frequencies of those SNPs in animals with birth weight greater than 4kg?",
        "How many samples are recorded as female?",
    ):
        print(json.dumps(query({"body": json.dumps({"query": demo})}, None), indent=2))
