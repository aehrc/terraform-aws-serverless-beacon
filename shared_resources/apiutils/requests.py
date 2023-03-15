import json

# 
# Start Thirdparty Code
# Code from https://github.com/EGA-archive/beacon2-ri-api
# Apache License 2.0
# 

import os
from typing_extensions import Self
from pydantic import BaseModel
from strenum import StrEnum
from typing import List, Optional, Union
from humps import camelize


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
    requested_granularity: Granularity = Granularity(BEACON_DEFAULT_GRANULARITY)


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
                self.query.include_resultset_responses = IncludeResultsetResponses(v)
            else:
                self.query.request_parameters[k] = v
        return self

    def summary(self):
        return {
            "apiVersion": self.meta.api_version,
            "requestedSchemas": self.meta.requested_schemas,
            "filters": self.query.filters,
            "requestParameters": self.query.request_parameters,
            "includeResultsetResponses": self.query.include_resultset_responses,
            "pagination": self.query.pagination.dict(),
            "requestedGranularity": self.query.requested_granularity,
            "testMode": self.query.test_mode
        }

# 
# End Thirdparty Code
# 


def parse_response(event):
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
