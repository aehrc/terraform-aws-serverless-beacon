import json
from typing import List

import pandas as pd
import requests
from strenum import StrEnum


class FilterType(StrEnum):
    ONTOLOGY = "ontology"
    ALPHANUMERIC = "alphanumeric"
    CUSTOM = "custom"


class BeaconV2:

    def __init__(self, api_url: str, auth_header: str) -> "BeaconV2":
        self._api_url = api_url
        self._auth_header = auth_header
        self._scope = None
        self._id = None
        self._filters = []
        self._g_variant_params = {}
        self._return_scope = None
        self._skip = 0
        self._limit = 1000

    def with_scope(self, scope) -> "BeaconV2":
        if scope not in [
            "individuals",
            "biosamples",
            "runs",
            "analyses",
            "g_variants",
            "cohorts",
            "datasets",
        ]:
            raise ValueError(f"Invalid scope: {scope}")
        if self._scope is not None:
            raise ValueError("Scope has already been set. Only one scope is allowed.")
        self._scope = scope
        return self

    def with_id(self, id: str) -> "BeaconV2":
        self._id = id
        return self

    def with_skip(self, skip: int):
        if not 0 <= skip:
            raise ValueError("Skip must be positive.")
        self._skip = skip
        return self

    def with_limit(self, limit: int):
        if not 0 < limit:
            raise ValueError("Limit must be positive and non-zero.")
        self._limit = limit
        return self

    def with_filter(
        self, filter_type: FilterType, filter_value: str, filter_scope: str
    ) -> "BeaconV2":
        if filter_type not in [
            FilterType.ONTOLOGY,
            FilterType.ALPHANUMERIC,
            FilterType.CUSTOM,
        ]:
            raise ValueError(f"Invalid filter type: {filter_type}")
        self._filters.append({"id": filter_value, "scope": filter_scope})
        return self

    def with_g_variant_params(
        self,
        assemblyId: str,
        referenceBases: str,
        alternateBases: str,
        start: List[int],
        end: List[int],
        referenceName: str,
    ) -> "BeaconV2":
        if self._scope != "g_variants":
            raise ValueError(
                "g_variant parameters can only be set if the scope is 'g_variants'"
            )
        if not (
            isinstance(start, list)
            and len(start) == 2
            and all(isinstance(i, int) for i in start)
        ):
            raise ValueError("Start must be a list of two integers.")
        if not (
            isinstance(end, list)
            and len(end) == 2
            and all(isinstance(i, int) for i in end)
        ):
            raise ValueError("End must be a list of two integers.")
        self._g_variant_params = {
            "assemblyId": assemblyId,
            "referenceBases": referenceBases if referenceBases else "N",
            "alternateBases": alternateBases if alternateBases else "N",
            "start": start,
            "end": end,
            "referenceName": referenceName,
        }
        return self

    def with_fetch_scope(self, return_scope) -> "BeaconV2":
        if return_scope not in [
            "individuals",
            "biosamples",
            "runs",
            "analyses",
            "g_variants",
            "cohorts",
            "datasets",
        ]:
            raise ValueError(f"Invalid return scope: {return_scope}")
        self._return_scope = return_scope
        return self

    def load(self):
        if self._scope is None:
            raise ValueError("Scope must be set before loading data.")
        if (
            self._scope == "g_variants"
            and self._return_scope is None
            and not self._g_variant_params
        ):
            raise ValueError(
                "g_variant parameters must be provided when the scope is 'g_variants', or use 'id' with return scope"
            )
        if (
            self._return_scope is not None
            and self._id is None
            or self._return_scope is None
            and self._id is not None
        ):
            raise ValueError("Must use 'id' with return scope")

        # Simulate data loading based on scope, ID, and filters
        print(f"Loading data for scope: {self._scope}")
        if self._id:
            print(f"Using ID: {self._id}")
        print(f"Using filters: {self._filters}")
        if self._scope == "g_variants":
            print(f"With g_variant parameters: {self._g_variant_params}")
        if self._return_scope:
            print(f"Fetching related scope: {self._return_scope}")

        body = {
            "query": {
                "pagination": {"skip": self._skip, "limit": self._limit},
                "filters": self._filters,
                "requestedGranularity": "record",
            },
            "meta": {"apiVersion": "v2.0"},
        }

        if not self._id:
            url = f"{self._api_url}/{self._scope}"
        else:
            url = f"{self._api_url}/{self._scope}/{self._id}/{self._return_scope}"

        print(f"Payload: {json.dumps(body)}")
        print(f"URL: {url}")

        headers = {
            "Authorization": self._auth_header,
            "Content-Type": "application/json",
        }

        response = requests.post(url, headers=headers, data=json.dumps(body))

        if not response.ok:
            print("Status", response.status_code)
            print("Response", response.text)
            raise Exception("Unable to call API on user behalf.")

        return response.json()


def normalise_response(data: dict):
    df = pd.json_normalize(data, ["response", "resultSets", "results"], max_level=0)
    cols = list(df.columns)

    if "id" in cols:
        cols.insert(0, cols.pop(cols.index("id")))
        df = df[cols]

    dicts = df.to_dict(orient="records")

    return (df, dicts)


if __name__ == "__main__":
    import os

    url = f"https://{os.environ['SBEACON_API_URL']}/prod"
    header = f"Bearer {os.environ['SBEACON_TEST_TOKEN']}"
    data = (
        BeaconV2(url, header)
        .with_scope("individuals")
        .with_skip(0)
        .with_limit(5)
        .load()
    )
    df, dicts = normalise_response(data)

    print(df.head())
    print(dicts)
