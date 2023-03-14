import json

#
# Start Thirdparty Code
# Code from https://github.com/EGA-archive/beacon2-ri-api
# Apache License 2.0
#

import os
import re
from typing_extensions import Self
from pydantic import BaseModel
from strenum import StrEnum
from typing import List, Optional, Union
from humps import camelize


CURIE_REGEX = r'^([a-zA-Z0-9]*):\/?[a-zA-Z0-9]*$'
BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_DEFAULT_GRANULARITY = os.environ['BEACON_DEFAULT_GRANULARITY']


class CamelModel(BaseModel):
    class Config:
        alias_generator = camelize
        allow_population_by_field_name = True


class IncludeResultsetResponses(StrEnum):
    ALL = "ALL",
    HIT = "HIT",
    MISS = "MISS",
    NONE = "NONE"


class Similarity(StrEnum):
    EXACT = "exact",
    HIGH = "high",
    MEDIUM = "medium",
    LOW = "low"


class Operator(StrEnum):
    EQUAL = "=",
    LESS = "<",
    GREATER = ">",
    NOT = "!",
    LESS_EQUAL = "<=",
    GREATER_EQUAL = ">="


class Granularity(StrEnum):
    BOOLEAN = "boolean",
    COUNT = "count",
    RECORD = "record"


class OntologyFilter(CamelModel):
    id: str
    scope: Optional[str] = None
    include_descendant_terms: bool = False
    similarity: Similarity = Similarity.EXACT


class AlphanumericFilter(CamelModel):
    id: str
    value: Union[str, List[int]]
    scope: Optional[str] = None
    operator: Operator = Operator.EQUAL


class CustomFilter(CamelModel):
    id: str
    scope: Optional[str] = None


class Pagination(CamelModel):
    skip: int = 0
    limit: int = 10


class RequestMeta(CamelModel):
    requested_schemas: List[str] = []
    # CHANGE: read constant from Terraform
    api_version: str = BEACON_API_VERSION


class RequestQuery(CamelModel):
    filters: List[dict] = []
    include_resultset_responses: IncludeResultsetResponses = IncludeResultsetResponses.HIT
    pagination: Pagination = Pagination()
    request_parameters: dict = {}
    test_mode: bool = False
    # CHANGE: read constant from Terraform
    requested_granularity: Granularity = Granularity(
        BEACON_DEFAULT_GRANULARITY)


class RequestParams(CamelModel):
    meta: RequestMeta = RequestMeta()
    query: RequestQuery = RequestQuery()

    # TODO update to parse body of API gateway POST and GET requests
    # CHANGE: parse API gateway request
    def from_request(self, query_params) -> Self:
        for k, v in query_params.items():
            if k == "requestedSchema":
                self.meta.requested_schemas = [v]
            elif k == "skip":
                self.query.pagination.skip = int(v)
            elif k == "limit":
                self.query.pagination.limit = int(v)
            elif k == "includeResultsetResponses":
                self.query.include_resultset_responses = IncludeResultsetResponses(
                    v)
            else:
                self.query.request_parameters[k] = v
        return self

    def summary(self):
        return {
            "apiVersion": self.meta.api_version,
            "requestedSchemas": self.meta.requested_schemas,
            "filters": self.query.filters,
            "req_params": self.query.request_parameters,
            "includeResultsetResponses": self.query.include_resultset_responses,
            "pagination": self.query.pagination.dict(),
            "requestedGranularity": self.query.requested_granularity,
            "testMode": self.query.test_mode
        }

# TODO use this function in query maker
# CHANGE: simplify only to perform object parsing


def parse_filters(filters: List[dict]) -> dict:
    for filter in filters:
        # accept string filters
        if isinstance(filter, str):
            filter = {"id": filter}
        if "value" in filter:
            filter = AlphanumericFilter(**filter)
        elif "similarity" in filter or "includeDescendantTerms" in filter or re.match(CURIE_REGEX, filter["id"]):
            filter = OntologyFilter(**filter)
        else:
            filter = CustomFilter(**filter)

        yield filter

#
# End Thirdparty Code
#


class QueryParams(CamelModel):
    start: List[int]
    end: List[int]
    assembly_id: str
    reference_name: str
    reference_bases: str = 'N'
    alternate_bases: str = 'N'
    variant_min_length: int = 0
    variant_max_length: int = -1
    allele: str = None
    geneId: str = None
    aminoacid_change: str = None
    variant_type: str = None


def parse_request(event):
    body_dict = dict()
    if event['httpMethod'] == 'POST':
        try:
            body_dict = json.loads(event.get('body') or '{}')
        except ValueError:
            pass
            # return bad_request(errorMessage='Error parsing request body, Expected JSON.')
    params = event.get('queryStringParameters', None) or dict()
    request_params = RequestParams(**body_dict).from_request(params)

    return request_params


def parse_request_params(request: RequestParams):
    req_params: dict = request.query.request_parameters
    return QueryParams(**req_params)
