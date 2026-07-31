import json
from typing import List, Optional

import pandas as pd
import requests
from strenum import StrEnum

# This fork's native Illumina endpoints (lambda/getSnps, getSamples,
# getGenotypes) plus the upstream Beacon entity scopes, so the same SDK works
# against either deployment. Confirm the route paths in api-*.tf before relying
# on the native three.
NATIVE_SCOPES = ("snps", "samples", "genotypes")

BEACON_SCOPES = (
    "individuals",
    "biosamples",
    "runs",
    "analyses",
    "g_variants",
    "cohorts",
    "datasets",
)

VALID_SCOPES = NATIVE_SCOPES + BEACON_SCOPES

# Beacon v2 spells not-equal "!", not "!=" (ats-request-body-schema.json,
# AlphanumericFilter.operator).
VALID_OPERATORS = ("=", "<", ">", "!", ">=", "<=")

# requestedGranularity enum from ats-request-body-schema.json.
VALID_GRANULARITIES = ("boolean", "count", "aggregated", "record")

# pagination.limit maximum from ats-request-body-schema.json.
MAX_LIMIT = 100000


class FilterType(StrEnum):
    ONTOLOGY = "ontology"
    ALPHANUMERIC = "alphanumeric"
    CUSTOM = "custom"


class BeaconV2:

    def __init__(self, api_url: str, auth_header: str) -> None:
        self._api_url = api_url.rstrip("/")
        self._auth_header = auth_header
        self._scope = None
        self._id = None
        self._filters = []
        self._g_variant_params = None
        self._return_scope = None
        self._granularity = "record"
        self._skip = 0
        self._limit = 1000

    # ------------------------------------------------------------------ scope
    def with_scope(self, scope) -> "BeaconV2":
        if scope not in VALID_SCOPES:
            raise ValueError(f"Invalid scope: {scope}")
        if self._scope is not None:
            raise ValueError("Scope has already been set. Only one scope is allowed.")
        self._scope = scope
        return self

    def with_id(self, id: str) -> "BeaconV2":
        self._id = id
        return self

    def with_skip(self, skip: int) -> "BeaconV2":
        if skip < 0:
            raise ValueError("Skip must be positive.")
        self._skip = skip
        return self

    def with_limit(self, limit: int) -> "BeaconV2":
        if limit <= 0:
            raise ValueError("Limit must be positive and non-zero.")
        if limit > MAX_LIMIT:
            raise ValueError(f"Limit must not exceed {MAX_LIMIT}.")
        self._limit = limit
        return self

    def with_granularity(self, granularity: str) -> "BeaconV2":
        if granularity not in VALID_GRANULARITIES:
            raise ValueError(f"Invalid granularity: {granularity}")
        self._granularity = granularity
        return self

    # ----------------------------------------------------------------- filters
    def with_filter(
        self,
        filter_type: FilterType,
        filter_value: str,
        filter_scope: str,
        operator: Optional[str] = None,
        value: Optional[str] = None,
    ) -> "BeaconV2":
        """
        Add a Beacon v2 filter.

        Ontology:     with_filter('ontology', 'PATO:0000383', 'individuals')
        Alphanumeric: with_filter('alphanumeric', 'birth_weight_kg', 'individuals', '>', '4')

        The previous implementation accepted an operator-less {id, scope} dict
        only, so every numeric condition ("birth weight greater than 4kg") was
        silently discarded before the request was built.
        """
        if filter_type not in tuple(FilterType):
            raise ValueError(f"Invalid filter type: {filter_type}")
        if filter_scope not in VALID_SCOPES:
            raise ValueError(f"Invalid filter scope: {filter_scope}")

        if filter_type == FilterType.ALPHANUMERIC:
            if operator is None:
                operator = "="
            if operator not in VALID_OPERATORS:
                raise ValueError(f"Invalid operator: {operator}")
            if value is None:
                raise ValueError(
                    "Alphanumeric filters need a value, e.g. "
                    "with_filter('alphanumeric', 'sex', 'individuals', '=', 'female')"
                )
            self._filters.append(
                {
                    "id": filter_value,
                    "operator": operator,
                    "value": str(value),
                    "scope": filter_scope,
                }
            )
        else:
            self._filters.append({"id": filter_value, "scope": filter_scope})
        return self

    # ------------------------------------------------------------------ region
    def with_g_variant(
        self,
        assemblyId: str,
        referenceBases: str,
        alternateBases: str,
        start: List[int],
        end: List[int],
        referenceName: str,
    ) -> "BeaconV2":
        # Bounds per g-variants-request-parameters.json: start is 1-2 integers
        # >= 0; end is 0-2 integers >= 1. A defaulted end of [0] is invalid.
        if not (isinstance(start, list) and all(isinstance(i, int) for i in start)):
            raise ValueError("Start must be a list of integers.")
        if not 1 <= len(start) <= 2:
            raise ValueError("Start must contain one or two positions.")
        if any(i < 0 for i in start):
            raise ValueError("Start positions must be 0 or greater.")
        if not (isinstance(end, list) and all(isinstance(i, int) for i in end)):
            raise ValueError("End must be a list of integers.")
        if len(end) > 2:
            raise ValueError("End must contain at most two positions.")
        if any(i < 1 for i in end):
            raise ValueError("End positions must be 1 or greater.")
        self._g_variant_params = {
            "assemblyId": assemblyId,
            "referenceBases": referenceBases if referenceBases else "N",
            "alternateBases": alternateBases if alternateBases else "N",
            "start": start,
            "end": end,
            "referenceName": str(referenceName),
        }
        return self

    def with_region(
        self,
        chromosome: str = None,
        start: int = None,
        end: int = None,
        assembly_id: str = None,
    ) -> "BeaconV2":
        """
        Express a genomic range.

        Against the native endpoints (/snps, /samples, /genotypes) this becomes
        alphanumeric filters on the snp table's own chromosome and coordinate
        columns. Those handlers read query.filters; they do not read
        query.requestParameters, and there is no /g_variants route in this
        deployment to send one to.

        Filtering on the stored coordinate also removes the 0-based/1-based
        question: manifest coordinates are 1-based, and so is "position 1 to
        50,000" as a producer means it.

        Against a stock sBeacon it falls back to a Beacon g_variant request.
        """
        if self._scope is None:
            raise ValueError("Set the scope before adding a region.")

        if self._scope not in NATIVE_SCOPES:
            return self.with_g_variant(
                assembly_id or "",
                "N",
                "N",
                [int(start)],
                [int(end)],
                str(chromosome),
            )

        # chromosome and coordinate live on the snp table regardless of which
        # endpoint is being queried.
        if chromosome not in (None, "", "unknown"):
            self.with_filter(
                FilterType.ALPHANUMERIC, "chromosome", "snps", "=", str(chromosome)
            )
        if start is not None:
            self.with_filter(
                FilterType.ALPHANUMERIC, "coordinate", "snps", ">=", str(int(start))
            )
        if end is not None:
            self.with_filter(
                FilterType.ALPHANUMERIC, "coordinate", "snps", "<=", str(int(end))
            )
        return self

    def with_fetch_scope(self, return_scope) -> "BeaconV2":
        if return_scope not in VALID_SCOPES:
            raise ValueError(f"Invalid return scope: {return_scope}")
        self._return_scope = return_scope
        return self

    # -------------------------------------------------------------------- load
    def _headers(self):
        return {
            "Authorization": self._auth_header,
            "Content-Type": "application/json",
        }

    def _post(self, url, body):
        print(f"URL: {url}")
        print(f"Payload: {json.dumps(body)}")
        response = requests.post(
            url, headers=self._headers(), data=json.dumps(body), timeout=60
        )
        if not response.ok:
            print("Status", response.status_code)
            print("Response", response.text[:1000])
            raise Exception(
                f"Beacon request failed ({response.status_code}) for {url}. "
                "Check the scope, filters and your token."
            )
        return response.json()

    @staticmethod
    def _results(payload):
        result_sets = payload.get("response", {}).get("resultSets") or [{}]
        return result_sets[0].get("results") or []

    def load(self):
        if self._scope is None:
            raise ValueError("Scope must be set before loading data.")
        if (
            self._scope == "g_variants"
            and self._return_scope is None
            and not self._g_variant_params
        ):
            raise ValueError(
                "g_variant parameters must be provided when the scope is 'g_variants', "
                "or use 'id' with a return scope"
            )
        if (self._return_scope is None) != (self._id is None):
            raise ValueError("Must use 'id' together with a return scope")

        body = {
            "query": {
                "pagination": {"skip": self._skip, "limit": self._limit},
                "filters": self._filters,
                "requestedGranularity": self._granularity,
            },
            "meta": {"apiVersion": "v2.0"},
        }
        if self._g_variant_params:
            body["query"]["requestParameters"] = self._g_variant_params

        # Region query first, then pivot to another scope (e.g. which animals
        # carry variants in this window).
        if self._g_variant_params and self._scope in NATIVE_SCOPES:
            raise ValueError(
                "requestParameters is not served by the native endpoints. "
                "Use with_region(), which emits chromosome/coordinate filters."
            )

        if self._g_variant_params and self._scope != "g_variants":
            payload = self._post(f"{self._api_url}/g_variants", body)
            variants = self._results(payload)
            print(f"Variant ids: {len(variants)}")
            if not variants:
                raise ValueError("No variants found for the given parameters.")

            del body["query"]["requestParameters"]
            records = []
            for variant in variants:
                vid = variant["variantInternalId"]
                url = f"{self._api_url}/g_variants/{vid}/{self._scope}"
                for record in self._results(self._post(url, body)):
                    record.setdefault("variantInternalId", vid)
                    records.append(record)

            print(f"Records: {len(records)}")
            return {"response": {"resultSets": [{"results": records}]}}

        if not self._id:
            url = f"{self._api_url}/{self._scope}"
        else:
            url = f"{self._api_url}/{self._scope}/{self._id}/{self._return_scope}"

        payload = self._post(url, body)
        if not self._results(payload):
            raise ValueError(
                "No results found for the given parameters. Try relaxing a filter."
            )
        return payload


def normalise_response(data: dict):
    df = pd.json_normalize(data, ["response", "resultSets", "results"], max_level=0)
    cols = list(df.columns)

    if "id" in cols:
        cols.insert(0, cols.pop(cols.index("id")))
        df = df[cols]

    return (df, df.to_dict(orient="records"))


if __name__ == "__main__":
    import os

    url = f"https://{os.environ['SBEACON_API_URL']}/prod"
    header = f"Bearer {os.environ['SBEACON_TEST_TOKEN']}"
    data = (
        BeaconV2(url, header)
        .with_scope("individuals")
        .with_filter(FilterType.ALPHANUMERIC, "sex", "individuals", "=", "female")
        .with_limit(5)
        .load()
    )
    df, dicts = normalise_response(data)
    print(df.head())
