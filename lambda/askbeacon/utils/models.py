import os
from enum import Enum
from functools import lru_cache
from typing import List, Optional, Union

from docarray import BaseDoc
from docarray.typing import NdArray
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel, Field, field_validator

from shared import sheep_schema

# --------------------------------------------------------------------------- #
# LLM / embedding clients
# --------------------------------------------------------------------------- #
# Previously these were built at import time and indexed os.environ directly, so
# importing utils.models with an incomplete environment raised KeyError before a
# single line of handler code ran (and the Azure branch always evaluated, even
# on the OpenAI path). They are now lazily constructed and cached.


def _env(name, default=None, required=False):
    value = os.environ.get(name, default)
    if required and not value:
        raise RuntimeError(
            f"Environment variable {name} is required to build the LLM client."
        )
    return value


@lru_cache(maxsize=None)
def _clients():
    from langchain_openai import (
        AzureChatOpenAI,
        AzureOpenAIEmbeddings,
        ChatOpenAI,
        OpenAIEmbeddings,
    )

    json_mode = {"type": "json_object"}

    if os.environ.get("OPENAI_API_KEY"):
        print("USING OPENAI")
        model_name = _env("OPENAI_COMPLETIONS_MODEL_NAME", "gpt-4o-mini")
        # response_format is a first-class parameter; passing it through
        # model_kwargs is deprecated in langchain-openai >= 0.2 and warns/raises
        # depending on version. bind() is stable across versions.
        chat_json = ChatOpenAI(model=model_name, temperature=0).bind(
            response_format=json_mode
        )
        chat_text = ChatOpenAI(model=model_name, temperature=0)
        embeddings = OpenAIEmbeddings(
            model=_env("OPENAI_EMBEDDING_MODEL_NAME", "text-embedding-3-small")
        )
    else:
        print("USING AZURE")
        deployment = _env("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", required=True)
        api_version = _env("AZURE_OPENAI_API_VERSION", required=True)
        chat_json = AzureChatOpenAI(
            openai_api_version=api_version,
            azure_deployment=deployment,
            temperature=0,
        ).bind(response_format=json_mode)
        chat_text = AzureChatOpenAI(
            openai_api_version=api_version,
            azure_deployment=deployment,
            temperature=0,
        )
        # The old code passed model="gpt-4-128k" to the embeddings client. That
        # is a chat model, not an embedding model, and it does not produce the
        # 1536-dim vectors VecDBEntry declares below.
        embeddings = AzureOpenAIEmbeddings(
            azure_deployment=_env(
                "AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME", "firstcontact-embeddings"
            ),
            model=_env("AZURE_OPENAI_EMBEDDING_MODEL_NAME", "text-embedding-3-small"),
        )

    return chat_json, chat_text, embeddings


class _LazyProxy:
    """Attribute proxy that builds the real client on first use."""

    def __init__(self, index):
        self._index = index

    def __getattr__(self, item):
        return getattr(_clients()[self._index], item)


# llm_json / llm_text are wrapped as Runnables so `prompt | llm_json | parser`
# still composes, while the underlying client is only constructed on the first
# invocation (keeps imports - and unit tests - free of API keys).
llm_json = RunnableLambda(lambda x: _clients()[0].invoke(x), name="llm_json")
llm_text = RunnableLambda(lambda x: _clients()[1].invoke(x), name="llm_text")
embeddings_model = _LazyProxy(2)


class VecDBEntry(BaseDoc):
    term: str
    label: str
    scope: str
    embedding: NdArray[1536]


# --------------------------------------------------------------------------- #
# Scopes
# --------------------------------------------------------------------------- #


class ScopeEnum(str, Enum):
    """
    Scopes the deployed API accepts.

    This fork replaces the stock Beacon entity endpoints with native Illumina
    ones: lambda/ contains getSnps, getSamples and getGenotypes, and no
    getIndividuals, getBiosamples or getGenomicVariants. The upstream values are
    kept so the same SDK can still query a stock sBeacon.
    """

    # Native Illumina endpoints (this fork)
    SNPS = "snps"
    SAMPLES = "samples"
    GENOTYPES = "genotypes"

    # Upstream Beacon v2 entity scopes
    BIOSAMPLE = "biosamples"
    INDIVIDUALS = "individuals"
    RUNS = "runs"
    ANALYSES = "analyses"
    GENOMIC_VARIANTS = "g_variants"
    DATASETS = "datasets"
    COHORTS = "cohorts"
    UNKNOWN = "unknown"


class SheepScopeEnum(str, Enum):
    """
    Domain scopes the LLM reasons about.

    The model is far more reliable picking "snps" for a SNP question than
    "g_variants", so we let it answer in producer language and map to a
    Beacon-legal scope deterministically in code.
    """

    SNPS = "snps"
    SAMPLES = "samples"
    GENOTYPES = "genotypes"
    PHENOTYPES = "phenotypes"
    DATASETS = "datasets"
    UNKNOWN = "unknown"


# Set False to target a stock sBeacon (individuals / biosamples / g_variants)
# instead of this fork's native endpoints. This flag and the two tables below
# are the only things that need to change if the routes are renamed.
NATIVE_ILLUMINA_ENDPOINTS = True

# This fork: the domain scope IS the endpoint. There is no /phenotypes lambda,
# so phenotype questions are answered from the per-animal sample endpoint.
NATIVE_SCOPE_MAP = {
    SheepScopeEnum.SNPS: ScopeEnum.SNPS,
    SheepScopeEnum.GENOTYPES: ScopeEnum.GENOTYPES,
    SheepScopeEnum.SAMPLES: ScopeEnum.SAMPLES,
    SheepScopeEnum.PHENOTYPES: ScopeEnum.SAMPLES,
    # No getDatasets lambda in this fork - degrade to "scope unknown" rather
    # than routing to an endpoint that does not exist.
    SheepScopeEnum.DATASETS: ScopeEnum.UNKNOWN,
    SheepScopeEnum.UNKNOWN: ScopeEnum.UNKNOWN,
}

# Stock sBeacon equivalents, for querying an upstream deployment.
BEACON_SCOPE_MAP = {
    SheepScopeEnum.SNPS: ScopeEnum.GENOMIC_VARIANTS,
    SheepScopeEnum.GENOTYPES: ScopeEnum.GENOMIC_VARIANTS,
    SheepScopeEnum.SAMPLES: ScopeEnum.INDIVIDUALS,
    SheepScopeEnum.PHENOTYPES: ScopeEnum.INDIVIDUALS,
    SheepScopeEnum.DATASETS: ScopeEnum.DATASETS,
    SheepScopeEnum.UNKNOWN: ScopeEnum.UNKNOWN,
}


def to_beacon_scope(scope) -> ScopeEnum:
    if isinstance(scope, str):
        try:
            scope = SheepScopeEnum(scope)
        except ValueError:
            try:
                return ScopeEnum(scope)
            except ValueError:
                return ScopeEnum.UNKNOWN
    table = NATIVE_SCOPE_MAP if NATIVE_ILLUMINA_ENDPOINTS else BEACON_SCOPE_MAP
    return table.get(scope, ScopeEnum.UNKNOWN)


class GranularityEnum(str, Enum):
    RECORD = "record"
    COUNT = "count"
    BOOLEAN = "boolean"
    UNKNOWN = "unknown"


class AggregationEnum(str, Enum):
    """
    Post-query computation. Beacon itself only returns records/counts, so
    anything derived (allele frequency, genotype distribution) is handed to the
    analytics code-generation chain instead of being faked in the query.
    """

    NONE = "none"
    ALLELE_FREQUENCY = "allele_frequency"
    GENOTYPE_COUNTS = "genotype_counts"
    CALL_RATE = "call_rate"
    SUMMARY_STATS = "summary_stats"


class OperatorEnum(str, Enum):
    """
    Beacon v2 operator set. Note not-equal is "!", not "!=" - an LLM asked for
    an operator will almost always emit "!=", so _missing_ maps the common
    spellings onto the legal value rather than failing validation.
    """

    EQ = "="
    NE = "!"
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="


    @classmethod
    def _missing_(cls, value):
        aliases = {
            "!=": cls.NE,
            "<>": cls.NE,
            "not": cls.NE,
            "==": cls.EQ,
            "=>": cls.GTE,
            "=<": cls.LTE,
        }
        return aliases.get(str(value).strip())


class FilterTypeEnum(str, Enum):
    ALPHANUMERIC = "alphanumeric"
    ONTOLOGY = "ontology"


class Scope(BaseModel):
    scope: SheepScopeEnum = SheepScopeEnum.UNKNOWN


class Region(BaseModel):
    """
    Genomic region / SNP selection.

    Replaces the old `Variant` model. There is no GRCh38 here - positions come
    from the OvineSNP50 manifest, so we no longer invite the model to invent a
    human assembly id, and chromosome stays a string ("X", "0", "OAR").
    """

    success: bool = False
    chromosome: str = "unknown"
    start: Union[List[int], int, str] = "unknown"
    end: Union[List[int], int, str] = "unknown"
    snp_ids: List[str] = Field(default_factory=list)

    @field_validator("chromosome")
    @classmethod
    def _clean_chromosome(cls, v):
        if not v or str(v).lower() in {"unknown", "none", "null"}:
            return "unknown"
        v = str(v).strip()
        for prefix in ("chr", "chromosome", "oar"):
            if v.lower().startswith(prefix) and len(v) > len(prefix):
                candidate = v[len(prefix) :].strip("_ -")
                if candidate.upper() in sheep_schema.VALID_CHROMOSOMES:
                    return candidate.upper() if candidate.isalpha() else candidate
        if v.upper() in {"X", "Y"}:
            return v.upper()
        return v if v in sheep_schema.VALID_CHROMOSOMES else "unknown"

    def as_bounds(self):
        """Return (start, end) as Beacon-style integer lists, or (None, None)."""

        def _coerce(value):
            if isinstance(value, list):
                return [int(v) for v in value] or None
            if isinstance(value, int):
                return [value]
            if isinstance(value, str) and value.isdigit():
                return [int(value)]
            return None

        return _coerce(self.start), _coerce(self.end)


# Backwards compatibility for any module still importing `Variant`.
Variant = Region


class Filter(BaseModel):
    """
    A single query condition.

    The old model was `{term, scope}` only, which meant "birth weight greater
    than 4 kg" collapsed to the string "birth weight greater than 4kg" and was
    then thrown at the ontology vector search. Operators and values are now
    first-class, which is what a Beacon v2 alphanumeric filter needs anyway.
    """

    type: FilterTypeEnum = FilterTypeEnum.ALPHANUMERIC
    field: str = ""
    operator: OperatorEnum = OperatorEnum.EQ
    value: str = ""
    scope: SheepScopeEnum = SheepScopeEnum.UNKNOWN
    term: Optional[str] = None  # free text, used for ontology lookups

    @field_validator("value", mode="before")
    @classmethod
    def _stringify(cls, v):
        return "" if v is None else str(v)

    @property
    def resolved_field(self):
        return sheep_schema.resolve_field(self.field)

    def is_resolvable(self) -> bool:
        if self.type == FilterTypeEnum.ONTOLOGY:
            return bool(self.term or self.value)
        return bool(self.resolved_field) and self.value != ""

    def to_beacon_filter(self):
        """Beacon v2 filter object."""
        if self.type == FilterTypeEnum.ONTOLOGY:
            return {"id": self.term or self.value, "scope": to_beacon_scope(self.scope)}
        return {
            "id": self.resolved_field or self.field,
            "operator": self.operator.value,
            "value": self.value,
            "scope": to_beacon_scope(self.scope),
        }

    def describe(self) -> str:
        field = self.resolved_field or self.field or self.term or "?"
        return f"{field} {self.operator.value} {self.value}".strip()


class Filters(BaseModel):
    filters: List[Filter] = Field(default_factory=list)

    def resolvable(self):
        return [f for f in self.filters if f.is_resolvable()]

    def unresolved(self):
        return [f for f in self.filters if not f.is_resolvable()]


class Granularity(BaseModel):
    granularity: GranularityEnum = GranularityEnum.UNKNOWN


class Aggregation(BaseModel):
    aggregation: AggregationEnum = AggregationEnum.NONE
    group_by: List[str] = Field(default_factory=list)


class YesNo(BaseModel):
    # Defaults matter: the tolerant parser falls back to an empty instance, and
    # an unparseable validation must fail closed rather than raise.
    yes: bool = False
    reason: str = "The query could not be interpreted."


class GeneratedCodeAnalytics(BaseModel):
    code: str = ""
    files: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    feedback: List[str] = Field(default_factory=list)
