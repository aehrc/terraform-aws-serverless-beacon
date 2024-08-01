import os
from enum import Enum
from typing import List, Union

from docarray import BaseDoc
from docarray.typing import NdArray
from langchain_openai import (
    AzureChatOpenAI,
    AzureOpenAIEmbeddings,
    ChatOpenAI,
    OpenAIEmbeddings,
)
from pydantic import BaseModel

if os.environ.get("OPENAI_API_KEY"):
    print("USING OPENAI")
    llm_json = ChatOpenAI(
        model=os.environ["OPENAI_COMPLETIONS_MODEL_NAME"],
        model_kwargs={"response_format": {"type": "json_object"}},
    )

    llm_text = ChatOpenAI(
        model=os.environ["OPENAI_COMPLETIONS_MODEL_NAME"],
        model_kwargs={"response_format": {"type": "text"}},
    )

    embeddings_model = OpenAIEmbeddings(model=os.environ["OPENAI_EMBEDDING_MODEL_NAME"])
else:
    print("USING AZURE")
    llm_json = AzureChatOpenAI(
        openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        azure_deployment=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
        model="gpt-4-128k",
        model_kwargs={"response_format": {"type": "json_object"}},
    )

    llm_text = AzureChatOpenAI(
        openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        azure_deployment=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
        model="gpt-4-128k",
        model_kwargs={"response_format": {"type": "text"}},
    )
    embeddings_model = AzureOpenAIEmbeddings(
        azure_deployment="firstcontact-embeddings", model="gpt-4-128k"
    )


class VecDBEntry(BaseDoc):
    term: str
    label: str
    scope: str
    embedding: NdArray[1536]


class ScopeEnum(str, Enum):
    BIOSAMPLE = "biosamples"
    INDIVIDUALS = "individuals"
    RUNS = "runs"
    ANALYSES = "analyses"
    GENOMIC_VARIANTS = "g_variants"
    DATASETS = "datasets"
    COHORTS = "cohorts"
    UNKNOWN = "unknown"


class GranularityEnum(str, Enum):
    RECORD = "record"
    COUNT = "count"
    BOOLEAN = "boolean"
    UNKNOWN = "unknown"


class Scope(BaseModel):
    scope: ScopeEnum


class Variant(BaseModel):
    success: bool
    assembly_id: str = "unknown"
    chromosome: str = "unknown"
    start: Union[List[int], int, str] = "unknown"
    end: Union[List[int], int, str] = "unknown"


class Filter(BaseModel):
    term: str
    scope: ScopeEnum


class Filters(BaseModel):
    filters: List[Filter]


class Granularity(BaseModel):
    granularity: GranularityEnum


class YesNo(BaseModel):
    yes: bool
    reason: str


class GeneratedCodeAnalytics(BaseModel):
    code: str
    files: List[str]
    assumptions: List[str]
    feedback: List[str]
