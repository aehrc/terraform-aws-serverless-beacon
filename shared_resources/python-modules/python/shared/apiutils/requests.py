import json
from collections import defaultdict
from typing_extensions import Self
from typing import List, Optional, Tuple, Union

from pydantic import (
    BaseModel,
    Extra,
    ValidationError,
    PrivateAttr,
    constr,
    validator,
    parse_obj_as,
)
from strenum import StrEnum
from humps import camelize

from shared.utils import ENV_BEACON


#
# Thirdparty Code as annotated
# Code from https://github.com/EGA-archive/beacon2-ri-api
# Apache License 2.0
# CHANGES: using terraform constants, additional parsing of request_params and filters
#


CURIE_REGEX = r"^([a-zA-Z0-9]*):\/?[a-zA-Z0-9]*$"
BEACON_API_VERSION = ENV_BEACON.BEACON_API_VERSION
BEACON_DEFAULT_GRANULARITY = ENV_BEACON.BEACON_DEFAULT_GRANULARITY
BEACON_ENABLE_AUTH = ENV_BEACON.BEACON_ENABLE_AUTH


# Thirdparty Code
class CamelModel(BaseModel):
    class Config:
        alias_generator = camelize
        allow_population_by_field_name = True
        extra = Extra.forbid


class RequestQueryParams(CamelModel):
    start: List[int] = [0]
    end: List[int] = [0]
    assembly_id: str = ""
    reference_name: str = ""
    reference_bases: str = "N"
    alternate_bases: str = "N"
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
    ALL = ("ALL",)
    HIT = ("HIT",)
    MISS = ("MISS",)
    NONE = "NONE"


# Thirdparty Code
class Similarity(StrEnum):
    EXACT = ("exact",)
    HIGH = ("high",)
    MEDIUM = ("medium",)
    LOW = "low"


# Thirdparty Code
class Operator(StrEnum):
    EQUAL = ("=",)
    LESS = ("<",)
    GREATER = (">",)
    NOT = ("!",)
    LESS_EQUAL = ("<=",)
    GREATER_EQUAL = ">="


# Thirdparty Code
class Granularity(StrEnum):
    BOOLEAN = ("boolean",)
    COUNT = ("count",)
    RECORD = "record"


# Thirdparty Code
class OntologyFilter(CamelModel):
    id: constr(regex=CURIE_REGEX)
    scope: Optional[str] = None
    include_descendant_terms: bool = True
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
    include_resultset_responses: IncludeResultsetResponses = (
        IncludeResultsetResponses.HIT
    )
    pagination: Pagination = Pagination()
    request_parameters: RequestQueryParams = RequestQueryParams()
    test_mode: bool = False
    requested_granularity: Granularity = Granularity(BEACON_DEFAULT_GRANULARITY)
    _filters: dict() = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        self._filters = data.get("filters", [])

    @validator("filters", pre=True, each_item=True)
    def transform_filters(cls, term):
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
                self.query.include_resultset_responses = IncludeResultsetResponses(v)
            elif k == "requestedGranularity":
                self.query.requested_granularity = Granularity(v)
            elif k == "filters":
                filters = v.split(",")
                self.query.filters = parse_obj_as(
                    List[Union[AlphanumericFilter, OntologyFilter, CustomFilter]],
                    [{"id": term} for term in filters],
                )
                self.query._filters = filters
            else:
                req_params_dict[k] = v
        # query parameters related to variants
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
            "testMode": self.query.test_mode,
        }


# TODO create a decorator for lambda handlers
def parse_request(event) -> Tuple[RequestParams, str]:
    body_dict = dict()
    if event["httpMethod"] == "POST":
        try:
            body_dict = json.loads(event.get("body") or "{}")
        except ValueError:
            pass
    params = event.get("queryStringParameters", None) or dict()

    errors = None
    request_params = None
    status = 200

    try:
        request_params = RequestParams(**body_dict).from_request(params)
    except ValidationError as e:
        errors = defaultdict(list)
        for e in e.errors():
            errors[e["msg"]].append(".".join(e["loc"]))
        return request_params, dict(errors), 400

    if BEACON_ENABLE_AUTH:
        # either use belongs to a group or they are unauthorized
        groups = (
            event.get("requestContext", dict())
            .get("authorizer", dict())
            .get("claims", dict())
            .get("cognito:groups", "unauthorized")
        )
        groups = groups.split(",")
        authorized = (
            f"{request_params.query.requested_granularity}-access-user-group" in groups
        )

        # return unauthorized status
        if not authorized:
            return (
                None,
                {
                    "anauthorized_access": f"User does not belong to {request_params.query.requested_granularity}-access-user-group"
                },
                400,
            )

    return request_params, errors, status
