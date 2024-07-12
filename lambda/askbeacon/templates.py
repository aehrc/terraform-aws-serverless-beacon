from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)
from models import Filters, Granularity, Scope, Variant, YesNo, llm_json, llm_text

scope_extractor_template = """
INSTRUCTIONS
Given a user query, select the result scope to best suited for the query.
Return a JSON object formatted to look like:
{{
    scope: most appropriate scope to respond to the query, if unsure put null
}}

SCOPE MUST BE ONE OF
individuals: user expects indivdual or people entries to be returned
biosamples: user expects biosample or samples entries to be returned
runs: user explicitly mention runs entries to be returned
analyses: user explicitly mention analyses entries to be returned
datasets: user explicitly mention datasets entries to be returned
cohorts: user explicitly mention cohorts entries to be returned
g_variants: user explicitly expects only genomic variants or variants entries to be returned
unknown: if you cannot confidently pick any of the above

QUERY
{query}

OUTPUT
"""

variant_extractor_template = """
INSTRUCTIONS
Given a user query, extract the assembly, chromosome, start base and end base.
Return a JSON object formatted to look like:
{{
    success: true or false, if a none of the attributes could be identified
    assembly_id: what is the mentioned assembly name (eg: grch38, hg38, or something similar) if unsure use "unknown",
    chromosome: chromosome mentioned in the query (could be a number 1-22, X or Y), if unsure use "unknown",
    start: start base pair or position; single number or an array of two numbers, if unsure use "unknown",
    end: end base pair or position; single number or an array of two numbers, if unsure use "unknown",
}}

CONDITIONS
whenever a field is unsure; use "unknown"
Ensure all fields are valid JSON

QUERY
{query}

OUTPUT
"""

filter_extractor_template = """
INSTRUCTIONS
Does the query contain a set of conditions. Ignore anything that corresponds to a genomic variant (position, chromosome, assembly)
Return a JSON object with an array formatted to look like:
{{
    filters: [
        {{
            term: place only one condition term here,
            scope: what might be the scope of this condition, chose from "individuals", "biosamples" and "runs"
        }}
    ]
}}

CONDITIONS
filters: this is an array with objects having two attributes called "term" and "scope". Ignore genomic variants
term: please insert only one condition here, if there are many, use multiple objects in "filters" array

QUERY
{query}

OUTPUT
"""

granularity_extractor_template = """
INSTRUCTIONS
Does the query contain a set of conditions.
Return a JSON object with an array formatted to look like:
{{
    granularity: what kind of a return is expected, null if not found
}}

CANDIDATE GRANULARITIES
record: requesting actual data records
count: asking for cardinality or count
boolean: only interested in the existence of data
unknown: if any of the above types not be matched

QUERY
{query}

OUTPUT
"""


def extract_object(query, template, model):
    parser = PydanticOutputParser(pydantic_object=model)
    template = ChatPromptTemplate.from_template(
        template,
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    chain = template | llm_json | parser
    result = chain.invoke(query)
    return result


def get_extractor_chain(template, model):
    parser = PydanticOutputParser(pydantic_object=model)
    template = ChatPromptTemplate.from_template(
        template,
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    chain = template | llm_json | parser
    return chain


def _get_validator_chain():
    template = ChatPromptTemplate.from_template(
        """You are a query builder for GA4GH Beacon V2. You must only accept user queries that are strickly relevant to the GA4FH beacon V2 domain. 
INSTRUCTIONS
Queries must be a biologically relevant question related to genomic variants, individuals, biosamples, runs, analysis. Conditions can be anything related to health,
biosample collection or phenotypic information.

Consider the scenarios below.
- If user is just greeting, write a few word greeting along the lines "Hello, I am AskBeacon assistant. What did you have mind for sBeacon?"
lightly modify the greeting message to be creative.

Repond with JSON of the form;
{{
    yes: true or false
    reason: reason behind yes/no - as shortly as possible. don't mention anything from user query.
}}

HISTORY
{history}

QUERY
{query}

OUTPUT
"""
    )
    validator_chain = {
        "valid": template | llm_json | PydanticOutputParser(pydantic_object=YesNo),
        "query": RunnablePassthrough(),
    }

    return RunnableParallel(**validator_chain)


def get_validate_and_followup_chain():
    correction_template = ChatPromptTemplate.from_template(
        """BACKGROUND
You are a query builder for GA4GH Beacon V2. In a previous validation of the query it has failed.

QUERY ASKED BY USER
{query}
IN WAS INVALID BECAUSE
{reason}
INSTRUCTIONS
Generate a followup question for the user so they can rephrase their question correctly. If the error was caused by unsupported beacon query let them know that. 
If they have asked something illegal beyond beacon scope, let them know that.
"""
    )

    def invalid_followup(result):
        if result["valid"].yes:
            return {
                "valid": True,
                "response": "Would you like to add any other conditions?",
            }
        followup_chain = correction_template | llm_text

        return {
            "valid": False,
            "response": followup_chain.invoke(
                {"query": result["query"], "reason": result["valid"].reason}
            ).content,
        }

    return _get_validator_chain() | RunnableLambda(invalid_followup)


def get_data_extractor_map_chain():
    extractor_chain = {
        "scope": get_extractor_chain(scope_extractor_template, Scope),
        "filters": get_extractor_chain(filter_extractor_template, Filters),
        "variant": get_extractor_chain(variant_extractor_template, Variant),
        "granularity": get_extractor_chain(granularity_extractor_template, Granularity),
        "query": RunnablePassthrough(),
    }
    map_chain = RunnableParallel(**extractor_chain)
    return map_chain


def get_success_followup_chain():
    followup_template = ChatPromptTemplate.from_template(
        """BACKGROUND
You are a query builder for GA4GH Beacon V2. You must only accept user queries that are strickly relevant to the GA4FH beacon V2 domain. 
Queries must be a direct question related to genomic variants, individuals, biosamples, runs, analysis. Conditions can be anything related to health,
biosample collection or phenotypic information.

Your task is to observe user query, see what we have extracted, explain the how we have mapped diseases to ontology terms and generate a understandable response.
Information in the extracted section could be from a past conversation. So no need to comment on any relatedness mismatches you notice.

QUERY ASKED BY USER
{query}
YOU HAVE DISCOVERED FOLLOWING INFORMATION (IGNORE IF EMPTY)
{extracted}
YOU ARE RETURNING FOLLOWING ONTOLOGY TERMS (IGNORE IF EMPTY)
{terms}
INSTRUCTIONS
Generate a followup so that the user can provide more info if they want. If there are some extracted content, acknowledge that.
If there arent any, please advise them in less than 20 words. Note that following are the allowed information.
- scope
- granularity
- variant - only if scope is g_variants
- filters

If nothing much is needed, let them know you can add more if needed or validate and run query.
If you see terms, explain that queried terms are translated into ontology codes (format is "query" - "ontology code" - "label"), tell that in list form so user can map it.
Do not add conclusions or make assumptions. No need to validate relationship of terms to query.
"""
    )

    return followup_template | llm_text
