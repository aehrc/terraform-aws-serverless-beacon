import json
from copy import deepcopy
from typing import Dict

from shared.apiutils.router import LambdaRouter
from utils import templates
from utils.auth import authenticate_endpoint
from utils.db import search_db
from utils.models import (
    Filters,
    Granularity,
    GranularityEnum,
    Scope,
    ScopeEnum,
    Variant,
)

router = LambdaRouter()


@router.attach("/ask/query", "post", authenticate_endpoint)
def query(event, context):
    body_dict = json.loads(event.get("body"))
    query = body_dict.get("query", None)
    history = body_dict.get("history", dict())

    if not query:
        return {
            "success": False,
            "response_text": "Please submit your query again.",
            "history": dict(),
            "response_data": None,
        }

    # validate and respond
    validate_and_followup_chain = templates.get_validate_and_followup_chain()
    payload = {
        "history": "\n".join([f"{k}: {v}" for k, v in history.items()]),
        "query": query,
    }
    print(f"Invoke 'validate_and_followup_chain' {payload=}")
    response = validate_and_followup_chain.invoke(payload)

    if not response["valid"]:
        print(f"Validation Failed: {query=} {response=}")
        return {
            "success": False,
            "response_text": response["response"],
            "response_data": None,
            "history": dict(),
        }
    print(f"Validation success: {query=} {response=}")

    # extract data
    extractor_chain = templates.get_data_extractor_map_chain()
    print(f"Invoke 'extractor_chain' {query=}")
    result: Dict[str, Scope | Filters | Granularity | Variant] = extractor_chain.invoke(
        query
    )
    extracted_data = dict()
    next_history = deepcopy(history)

    # TODO instead of "provided" use actual arrays, but pass "provided" to LLM
    # this way I have full extraction history

    if (scope := result["scope"]).scope != ScopeEnum.UNKNOWN:
        extracted_data["scope"] = scope.model_dump(mode="json")["scope"]
        next_history["scope"] = extracted_data["scope"]

    if len(result["filters"].filters) > 0:
        filters = result["filters"]
        filters = filters.model_dump(mode="json")["filters"]
        hits = []
        for filter in filters:
            entries = search_db(filter["term"])
            for entry, score in entries:
                hits.append(
                    {
                        "scope": filter["scope"],
                        "term": entry.term,
                        "score": score,
                        "label": entry.label,
                        "query": filter["term"],
                    }
                )
        extracted_data["filters"] = hits
        if len(hits):
            next_history["filters"] = "provided"

    if (granularity := result["granularity"]).granularity != GranularityEnum.UNKNOWN:
        extracted_data["granularity"] = granularity.model_dump(mode="json")[
            "granularity"
        ]
        next_history["granularity"] = extracted_data["granularity"]

    if (variant := result["variant"]).success:
        extracted_data["variant"] = {
            k: v
            for k, v in variant.model_dump(mode="json").items()
            if k != "succcess" and v != "unknown"
        }
        next_history["variant"] = "provided"

    success_followup_chain = templates.get_success_followup_chain()
    payload = {
        "query": query,
        "extracted": "\n".join([f"{k}: {v}" for k, v in next_history.items()]),
        "terms": "\n".join(
            [
                f"{hit['term']} - {hit['label']}"
                for hit in extracted_data.get("filters", [])
            ]
        ),
    }
    print(f"Invoke 'success_followup_chain' {payload=}")
    response = success_followup_chain.invoke(payload).content

    return {
        "response_data": extracted_data,
        "response_text": response,
        "history": next_history,
        "success": True,
    }


if __name__ == "__main__":
    event = {
        "body": json.dumps(
            {
                "query": "",
            }
        )
    }
    res = query(event, "")
    print(res)
    pass
