import json
import os
from typing_extensions import Self
from typing import List, Optional, Union

from pydantic import BaseModel, PrivateAttr, constr, validator
from strenum import StrEnum
from humps import camelize

#
# Thirdparty Code as annotated
# Code from https://github.com/EGA-archive/beacon2-ri-api
# Apache License 2.0
# CHANGES: using terraform constants, additional parsing of request_params and filters
#


CURIE_REGEX = r'^([a-zA-Z0-9]*):\/?[a-zA-Z0-9]*$'
BEACON_API_VERSION = os.environ['BEACON_API_VERSION']
BEACON_DEFAULT_GRANULARITY = os.environ['BEACON_DEFAULT_GRANULARITY']


# Thirdparty Code
class CamelModel(BaseModel):
    class Config:
        alias_generator = camelize
        allow_population_by_field_name = True


class RequestQueryParams(CamelModel):
    start: List[int] = [0]
    end: List[int] = [0]
    assembly_id: str = ''
    reference_name: str = ''
    reference_bases: str = 'N'
    alternate_bases: str = 'N'
    variant_min_length: int = 0
    variant_max_length: int = -1
    allele: Optional[str]
    geneId: Optional[str]
    aminoacid_change: Optional[str]
    variant_type: Optional[str]
    _user_params: dict() = PrivateAttr()
    
    def __init__(self, **data):
        super().__init__(**data)
        self._user_params = data


# Thirdparty Code
class IncludeResultsetResponses(StrEnum):
    ALL = "ALL",
    HIT = "HIT",
    MISS = "MISS",
    NONE = "NONE"


# Thirdparty Code
class Similarity(StrEnum):
    EXACT = "exact",
    HIGH = "high",
    MEDIUM = "medium",
    LOW = "low"


# Thirdparty Code
class Operator(StrEnum):
    EQUAL = "=",
    LESS = "<",
    GREATER = ">",
    NOT = "!",
    LESS_EQUAL = "<=",
    GREATER_EQUAL = ">="


# Thirdparty Code
class Granularity(StrEnum):
    BOOLEAN = "boolean",
    COUNT = "count",
    RECORD = "record"


# Thirdparty Code
class OntologyFilter(CamelModel):
    id: constr(regex=CURIE_REGEX)
    scope: Optional[str] = None
    include_descendant_terms: bool = False
    similarity: Similarity = Similarity.EXACT


# Thirdparty Code
class AlphanumericFilter(CamelModel):
    id: str
    value: Union[str, List[int]]
    scope: Optional[str] = None
    operator: Operator = Operator.EQUAL


# Thirdparty Code
class CustomFilter(CamelModel):
    id: str
    scope: Optional[str] = None


# Thirdparty Code
class Pagination(CamelModel):
    skip: int = 0
    limit: int = 10


# Thirdparty Code
class RequestMeta(CamelModel):
    requested_schemas: List[str] = []
    api_version: str = BEACON_API_VERSION


# Thirdparty Code
class RequestQuery(CamelModel):
    filters: List[Union[AlphanumericFilter, OntologyFilter, CustomFilter]] = []
    include_resultset_responses: IncludeResultsetResponses = IncludeResultsetResponses.HIT
    pagination: Pagination = Pagination()
    request_parameters: RequestQueryParams = RequestQueryParams()
    test_mode: bool = False
    requested_granularity: Granularity = Granularity(
        BEACON_DEFAULT_GRANULARITY)
    _filters: dict() = PrivateAttr()
    
    def __init__(self, **data):
        super().__init__(**data)
        self._filters = data.get('filters', [])

    @validator('filters', pre=True, each_item=True)
    def check_squares(cls, term):
        if isinstance(term, str):
            term = {"id": term}
        return term


# Thirdparty Code
class RequestParams(CamelModel):
    meta: RequestMeta = RequestMeta()
    query: RequestQuery = RequestQuery()

    # TODO update to parse body of API gateway POST and GET requests
    # CHANGE: parse API gateway request
    def from_request(self, query_params) -> Self:
        req_params_dict = dict()
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
                req_params_dict[k] = v
        if len(req_params_dict):
            self.query.request_parameters = RequestQueryParams(**req_params_dict)
        return self

    def summary(self):
        return {
            "apiVersion": self.meta.api_version,
            "requestedSchemas": self.meta.requested_schemas,
            "filters": self.query._filters,
            "req_params": self.query.request_parameters._user_params,
            "includeResultsetResponses": self.query.include_resultset_responses,
            "pagination": self.query.pagination.dict(),
            "requestedGranularity": self.query.requested_granularity,
            "testMode": self.query.test_mode
        }


# TODO create a decorator for lambda handlers
def parse_request(event) -> RequestParams:
    body_dict = dict()
    if event['httpMethod'] == 'POST':
        try:
            body_dict = json.loads(event.get('body') or '{}')
        except ValueError:
            pass
    params = event.get('queryStringParameters', None) or dict()
    request_params = RequestParams(**body_dict).from_request(params)

    return request_params
