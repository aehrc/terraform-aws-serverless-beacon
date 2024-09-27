import json
from collections import defaultdict
from typing import Annotated, List, Optional, Self, Tuple, Union

from humps import camelize
from pydantic import (
    BaseModel,
    ConfigDict,
    PrivateAttr,
    TypeAdapter,
    ValidationError,
    ValidationInfo,
    constr,
    field_validator,
    model_validator,
)
from pydantic.functional_validators import BeforeValidator
from shared.utils import ENV_BEACON, ENV_CONFIG
from strenum import StrEnum

#
# Thirdparty Code as annotated
# Code from https://github.com/EGA-archive/beacon2-ri-api
# Apache License 2.0
# CHANGES: using terraform constants, additional parsing of request_params and filters
#


# TODO friendly error messages (not too verbose)
CURIE_REGEX = r"^\w[^:]+:.+$"
BEACON_API_VERSION = ENV_BEACON.BEACON_API_VERSION
BEACON_DEFAULT_GRANULARITY = ENV_BEACON.BEACON_DEFAULT_GRANULARITY
BEACON_ENABLE_AUTH = ENV_BEACON.BEACON_ENABLE_AUTH
CONFIG_MAX_VARIANT_SEARCH_BASE_RANGE = ENV_CONFIG.CONFIG_MAX_VARIANT_SEARCH_BASE_RANGE


# Thirdparty Code
class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=camelize, populate_by_name=True, extra="forbid"
    )


class RequestQueryParams(CamelModel):
    start: List[int] = [0]
    end: List[int] = [0]
    assembly_id: str = ""
    reference_name: str = ""
    reference_bases: str = "N"
    alternate_bases: str = "N"
    variant_min_length: int = 0
    variant_max_length: int = -1
    allele: Optional[str] = None
    gene_id: Optional[str] = None
    aminoacid_change: Optional[str] = None
    variant_type: Optional[str] = None
    _user_params: dict = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        self._user_params = data

    @field_validator("start", "end")
    @classmethod
    def vallidate_base_positions(cls, base: list[int], info: ValidationInfo):
        # if base range is give; must not exeed limit
        if len(base) == 2:
            if base[0] >= base[1]:
                raise ValueError(f"Values in {info.field_name} must be ascending")
            elif abs(base[0] - base[1]) > CONFIG_MAX_VARIANT_SEARCH_BASE_RANGE:
                raise ValueError(
                    f"""Range in '{info.field_name}' exceeds max allowed ({CONFIG_MAX_VARIANT_SEARCH_BASE_RANGE})"""
                )
        return base

    @model_validator(mode="after")
    def validate_base_range(self):
        error_message = f"Base range should be positive and less than {CONFIG_MAX_VARIANT_SEARCH_BASE_RANGE}. Consider using start (eg: [100, 200]) and end (eg: [250, 300]) ranges or shorten the range between start and end positions (eg: start=[100], end=[200])"
        # if start and end is give; that must be within limit
        if (
            len(self.start) == 1
            and len(self.end) == 1
            and abs(self.start[0] - self.end[0]) > CONFIG_MAX_VARIANT_SEARCH_BASE_RANGE
        ):
            raise ValueError(error_message, ["start", "end"])
        # if start is a range and end is a base
        if len(self.start) == 2 and len(self.end) == 1:
            if abs(self.end[0] - self.start[0]) > CONFIG_MAX_VARIANT_SEARCH_BASE_RANGE:
                raise ValueError(error_message, ["start", "end"])
        # if start is a base and end is a range
        if len(self.start) == 1 and len(self.end) == 2:
            if abs(self.end[1] - self.start[0]) > CONFIG_MAX_VARIANT_SEARCH_BASE_RANGE:
                raise ValueError(error_message, ["start", "end"])
        return self


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
    id: constr(pattern=CURIE_REGEX)
    scope: Optional[str] = None
    include_descendant_terms: bool = True
    similarity: Similarity = Similarity.EXACT


# Thirdparty Code
class AlphanumericFilter(CamelModel):
    id: str
    value: Union[str, int]
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


def transform_filters(term):
    if isinstance(term, str):
        term = {"id": term}
    return term


# Thirdparty Code
class RequestQuery(CamelModel):
    filters: Annotated[
        List[Union[AlphanumericFilter, OntologyFilter, CustomFilter]],
        BeforeValidator(transform_filters),
    ] = []
    include_resultset_responses: IncludeResultsetResponses = (
        IncludeResultsetResponses.HIT
    )
    pagination: Pagination = Pagination()
    request_parameters: RequestQueryParams = RequestQueryParams()
    test_mode: bool = False
    requested_granularity: Granularity = Granularity(BEACON_DEFAULT_GRANULARITY)
    _filters: dict = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        self._filters = data.get("filters", [])


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
                adapter = TypeAdapter(
                    List[Union[AlphanumericFilter, OntologyFilter, CustomFilter]]
                )
                self.query._filters = filters
                self.query.filters = adapter.validate_python(
                    [{"id": term} for term in filters]
                )
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
            "pagination": self.query.pagination.model_dump(),
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
        errors = defaultdict(set)

        for e in e.errors():
            errors[e["msg"]].add(".".join([str(l) for l in e["loc"]]))

        return request_params, dict({k: list(v) for k, v in errors.items()}), 400

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
