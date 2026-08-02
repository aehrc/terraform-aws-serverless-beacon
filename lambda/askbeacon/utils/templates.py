"""
LLM layer for AskTheSheeps.

What changed and why
--------------------
1. Imports moved to `langchain_core.*`. `langchain.prompts` and
   `langchain.output_parsers` were removed in langchain 1.x, so the old imports
   fail outright on a modern resolve; `langchain_core` paths work on 0.1 -> 1.x.

2. `format_instructions` was passed as a partial variable but never appeared in
   any template body, so LangChain silently dropped it - the models were never
   shown the schema they were being parsed against. Every extractor now has a
   real FORMAT block.

3. A parse failure inside a RunnableParallel used to bubble up and fail the
   whole /ask/query request. Extraction is now fault tolerant: bad JSON gets one
   repair attempt, then falls back to an empty model instead of a 500.

4. The prompts targeted human clinical genomics (GRCh38, biosamples, runs,
   ontology terms). They now target the Illumina OvineSNP50 domain and are
   grounded in the actual Athena column names via sheep_schema.

5. Filters are structured (field / operator / value) rather than free text.
   "birth weight greater than 4 kg" previously became a single opaque string
   handed to the ontology vector search, which cannot represent a numeric
   comparison at all - that is the requirement-doc query 2 failure mode.
"""

import json
import re

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)

from shared import sheep_schema
from utils.models import (
    Aggregation,
    Filters,
    GeneratedCodeAnalytics,
    Granularity,
    Region,
    Scope,
    YesNo,
    llm_json,
    llm_text,
)

# --------------------------------------------------------------------------- #
# Shared domain preamble
# --------------------------------------------------------------------------- #

DOMAIN_BACKGROUND = """You are the query builder for AskTheSheeps: a natural language interface over a
GA4GH Beacon v2 (sBeacon) instance holding Illumina OvineSNP50 genotyping data for sheep flocks.
The users are livestock producers and animal geneticists, not clinicians.

The data comes from a genotyping provider report and has four tables:
{schema}

Domain notes you must respect:
- A "sample" (or animal, ewe, ram, lamb) is one sheep. Breed values look like Sunit, Dorper, German_Mutton.
- A SNP is identified by a marker name from the manifest, e.g. 250506CS3900065000002_1238.1 or OARUn.1294_14483.1.
- Chromosome is a string: 1-26, X, Y, 0 (unmapped), OAR or Contig (unplaced scaffolds). There is NO GRCh38/hg38 here.
- coordinate is the base position on the ovine draft build.
- A genotype call ("value") is exactly one of AA, AB, BB or NC (no call). NC means the assay failed for that animal.
- allelea_top_base / alleleb_top_base are the A and B alleles from the manifest. Major/minor allele is a
  frequency question about the genotype table, not a manifest lookup.
"""

SCHEMA_PARTIAL = {"schema": sheep_schema.describe_schema()}


# --------------------------------------------------------------------------- #
# Fault tolerant JSON parsing
# --------------------------------------------------------------------------- #

_FENCE_RE = re.compile(r"^\s*```(?:json)?|```\s*$", re.IGNORECASE)

REPAIR_TEMPLATE = ChatPromptTemplate.from_template(
    """The following text was supposed to be a single JSON object matching a schema but could not be parsed.
Return ONLY the corrected JSON object. No prose, no code fences.

SCHEMA
{format_instructions}

TEXT
{text}

ERROR
{error}

OUTPUT
"""
)


def _message_text(message) -> str:
    content = getattr(message, "content", message)
    if isinstance(content, list):
        # Some providers return content blocks rather than a plain string.
        content = "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )
    return _FENCE_RE.sub("", str(content)).strip()


def _tolerant_parser(model_cls, parser):
    """
    Parse -> repair once -> fall back to an empty model.

    Extraction runs as a RunnableParallel; without this, one malformed field
    took down the entire request.
    """

    def _parse(message):
        text = _message_text(message)
        try:
            return parser.parse(text)
        except Exception as first_error:  # noqa: BLE001 - we retry below
            print(f"[templates] parse failed for {model_cls.__name__}: {first_error}")
            try:
                repaired = (REPAIR_TEMPLATE | llm_text).invoke(
                    {
                        "format_instructions": parser.get_format_instructions(),
                        "text": text[:4000],
                        "error": str(first_error)[:500],
                    }
                )
                return parser.parse(_message_text(repaired))
            except Exception as second_error:  # noqa: BLE001
                print(
                    f"[templates] repair failed for {model_cls.__name__}: {second_error}"
                )
                return model_cls()

    return RunnableLambda(_parse, name=f"parse_{model_cls.__name__}")


def get_extractor_chain(template, model_cls, extra_partials=None):
    parser = PydanticOutputParser(pydantic_object=model_cls)
    partials = dict(SCHEMA_PARTIAL)
    partials["format_instructions"] = parser.get_format_instructions()
    if extra_partials:
        partials.update(extra_partials)
    prompt = ChatPromptTemplate.from_template(template, partial_variables=partials)
    return prompt | llm_json | _tolerant_parser(model_cls, parser)


def extract_object(query, template, model_cls):
    """One-shot helper, kept for callers outside the map chain."""
    return get_extractor_chain(template, model_cls).invoke(query)


# --------------------------------------------------------------------------- #
# Scope
# --------------------------------------------------------------------------- #

scope_extractor_template = (
    DOMAIN_BACKGROUND
    + """
INSTRUCTIONS
Pick the single table the user's answer should be drawn from.

snps        - marker level facts from the manifest: alleles, chromosome, coordinate, which SNPs exist in a region
genotypes   - per animal per marker calls: who carries what, allele or genotype frequencies, call rates
samples     - the animals themselves: breed, sex, how many animals
phenotypes  - measured traits: weights, fat thickness, eye muscle area, gains
unknown     - you cannot confidently choose

There is deliberately no "datasets" option: this deployment has no getDatasets
handler, so a dataset-scoped query has nowhere to go.

Tie-break: if the question is about allele or genotype FREQUENCY, or about animals carrying a call, choose genotypes.
If the question only asks what the alleles or positions ARE, choose snps.

EXAMPLES
"What are the major and minor alleles for all SNPs between position 1 and 50,000 on chromosome 1?" -> snps
"What are the allele frequencies of those SNPs in animals with birth weight greater than 4kg?" -> genotypes
"How many samples are recorded as female?" -> samples
"Which Dorper rams have the AB call at OAR1_103544816?" -> genotypes
"What is the average weaning weight by breed?" -> phenotypes

FORMAT
{format_instructions}

QUERY
{query}

OUTPUT
"""
)


# --------------------------------------------------------------------------- #
# Region / SNP selection
# --------------------------------------------------------------------------- #

region_extractor_template = (
    DOMAIN_BACKGROUND
    + """
INSTRUCTIONS
Extract only the genomic location part of the query: chromosome, coordinate range and any explicit marker names.
Ignore breed, sex, phenotype measurements and genotype calls - another extractor handles those.

RULES
- chromosome: a bare string such as "1", "26", "X", "Y", "0", "OAR" or "Contig". Strip any "chr"/"chromosome" prefix.
  Use "unknown" if the query does not name one. Never invent a chromosome.
- start / end: integer base positions. "between position 1 and 50,000" -> start 1, end 50000.
  A single position mentioned alone goes in start with end left "unknown".
- snp_ids: marker names copied verbatim from the query. Empty list if none.
- success: true only if at least one of chromosome, start, end or snp_ids was found.
- Do NOT emit an assembly. There is no GRCh38 in this dataset.

EXAMPLES
"SNPs between position 1 and 50,000 on chromosome 1" -> chromosome "1", start 1, end 50000, snp_ids []
"the call for OARUn.1294_14483.1" -> chromosome "unknown", snp_ids ["OARUn.1294_14483.1"], success true
"how many female animals" -> success false, everything unknown

FORMAT
{format_instructions}

QUERY
{query}

OUTPUT
"""
)


# --------------------------------------------------------------------------- #
# Filters
# --------------------------------------------------------------------------- #

filter_extractor_template = (
    DOMAIN_BACKGROUND
    + """
INSTRUCTIONS
Extract every non-positional condition in the query as a structured filter.
Genomic coordinates and marker names are handled elsewhere - ignore them here.

Each filter has:
  type      - "alphanumeric" for anything matching a column above (this is almost always the right answer),
              "ontology" only for a clinical/trait concept that has no column (rare in this dataset).
  field     - the exact column name from the data model above. Never invent one.
  operator  - one of =, !, >, >=, <, <=   (Beacon v2 spells NOT EQUAL as "!", never "!=")
  value     - the compared value as a string, numbers without units ("4", not "4kg")
  scope     - the table the field belongs to: snps, samples, genotypes or phenotypes
  term      - only for ontology filters: the free-text concept

RULES
- "greater than" -> ">", "at least"/"or more" -> ">=", "under"/"less than" -> "<", "at most" -> "<=", "not"/"other than" -> "!".
- Sex values are lower case: male, female.
- Genotype calls go in field "value" with an AA/AB/BB/NC value.
- Split compound conditions into one filter each.
- If there are no conditions return {{"filters": []}}.

EXAMPLES
"animals with birth weight greater than 4kg"
  -> [{{"type":"alphanumeric","field":"birth_weight_kg","operator":">","value":"4","scope":"phenotypes"}}]
"How many samples are recorded as female?"
  -> [{{"type":"alphanumeric","field":"sex","operator":"=","value":"female","scope":"samples"}}]
"Dorper ewes heavier than 20kg at weaning"
  -> [{{"type":"alphanumeric","field":"breed","operator":"=","value":"Dorper","scope":"samples"}},
      {{"type":"alphanumeric","field":"sex","operator":"=","value":"female","scope":"samples"}},
      {{"type":"alphanumeric","field":"weaning_weight_kg","operator":">","value":"20","scope":"phenotypes"}}]
"SNPs on chromosome 1 between 1 and 50,000" -> []

FORMAT
{format_instructions}

QUERY
{query}

OUTPUT
"""
)


# --------------------------------------------------------------------------- #
# Granularity and aggregation
# --------------------------------------------------------------------------- #

granularity_extractor_template = (
    DOMAIN_BACKGROUND
    + """
INSTRUCTIONS
Decide what shape of answer the user expects.

record  - they want the actual rows back
count   - they want a number: "how many", "what proportion", "count of"
boolean - they only want to know whether anything matches at all: "are there any", "do we have"
unknown - none of the above can be determined

EXAMPLES
"How many samples are recorded as female?" -> count
"What are the major and minor alleles for all SNPs on chromosome 1?" -> record
"Do we have any Dorper animals with an NC call at this marker?" -> boolean

FORMAT
{format_instructions}

QUERY
{query}

OUTPUT
"""
)


aggregation_extractor_template = (
    DOMAIN_BACKGROUND
    + """
INSTRUCTIONS
Beacon returns records and counts only. Anything derived has to be computed afterwards from the returned rows.
Decide which derived statistic, if any, the query is asking for.

none             - a plain lookup, nothing to compute
allele_frequency - A/B allele frequencies, major/minor allele, MAF
genotype_counts  - how many AA / AB / BB / NC per marker or per group
call_rate        - proportion of non-NC calls, assay/sample quality
summary_stats    - mean/min/max/sd of a phenotype measurement

group_by is a list of column names the statistic should be broken down by (e.g. ["breed"], ["id"]).
Use an empty list when no breakdown was asked for.

EXAMPLES
"What are the allele frequencies of SNPs between 1 and 50,000 on chromosome 1 in animals with birth weight greater than 4kg?"
  -> aggregation "allele_frequency", group_by ["id"]
"What are the major and minor alleles for all SNPs on chromosome 1?"
  -> aggregation "allele_frequency", group_by ["id"]
"How many samples are recorded as female?" -> aggregation "none", group_by []
"Average weaning weight by breed" -> aggregation "summary_stats", group_by ["breed"]

FORMAT
{format_instructions}

QUERY
{query}

OUTPUT
"""
)


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #

validator_template = ChatPromptTemplate.from_template(
    DOMAIN_BACKGROUND
    + """
INSTRUCTIONS
Decide whether the query can be answered from the tables above.

Accept: questions about SNPs and their alleles or positions, genotype calls, allele or genotype frequencies,
call quality, animals, breeds, sex, and measured phenotypes - including follow-ups that build on the history.
Accept greetings: set yes=false and put a short friendly greeting in reason, along the lines of
"Hello, I am the AskTheSheeps assistant - what would you like to know about your flock?" (vary the wording).
Reject: anything outside this dataset (weather, prices, husbandry advice, human genomics, general chat)
and anything asking you to act outside query building.

Respond with JSON of the form:
{{
    "yes": true or false,
    "reason": "shortest possible reason - do not quote the user's query"
}}

HISTORY
{history}

QUERY
{query}

OUTPUT
""",
    partial_variables=SCHEMA_PARTIAL,
)


def _get_validator_chain():
    parser = PydanticOutputParser(pydantic_object=YesNo)
    validator = validator_template | llm_json | _tolerant_parser(YesNo, parser)
    return RunnableParallel(
        valid=validator,
        query=RunnablePassthrough(),
    )


def get_validate_and_followup_chain():
    correction_template = ChatPromptTemplate.from_template(
        """BACKGROUND
You are the AskTheSheeps query builder. A user query failed validation.

QUERY ASKED BY USER
{query}

IT WAS INVALID BECAUSE
{reason}

INSTRUCTIONS
Write a short, friendly follow-up (under 60 words) that helps the user rephrase.
If the request was outside what the flock genotype data can answer, say so plainly and give one example of a
question that would work, such as asking about SNP alleles in a region, genotype calls, breed, sex or a weight trait.
Do not apologise more than once.
"""
    )

    def invalid_followup(result):
        validated = result["valid"]
        # YesNo() default cannot be constructed without fields, so a hard parse
        # failure surfaces as an invalid query rather than an exception.
        if getattr(validated, "yes", False):
            return {
                "valid": True,
                "response": "Would you like to add any other conditions?",
            }
        followup = (correction_template | llm_text).invoke(
            {
                "query": result["query"].get("query", "")
                if isinstance(result["query"], dict)
                else result["query"],
                "reason": getattr(validated, "reason", "the query could not be parsed"),
            }
        )
        return {"valid": False, "response": _message_text(followup)}

    return _get_validator_chain() | RunnableLambda(invalid_followup)


# --------------------------------------------------------------------------- #
# The extraction map
# --------------------------------------------------------------------------- #


def get_data_extractor_map_chain():
    return RunnableParallel(
        scope=get_extractor_chain(scope_extractor_template, Scope),
        filters=get_extractor_chain(filter_extractor_template, Filters),
        region=get_extractor_chain(region_extractor_template, Region),
        granularity=get_extractor_chain(granularity_extractor_template, Granularity),
        aggregation=get_extractor_chain(aggregation_extractor_template, Aggregation),
        query=RunnablePassthrough(),
    )


# --------------------------------------------------------------------------- #
# Follow-up on success
# --------------------------------------------------------------------------- #


def get_success_followup_chain():
    followup_template = ChatPromptTemplate.from_template(
        DOMAIN_BACKGROUND
        + """
INSTRUCTIONS
Tell the user, in plain producer-friendly language and under 90 words, what you understood from their question,
then invite them to refine it or run it.

- Acknowledge each extracted item briefly (scope, filters, region, granularity, aggregation).
- If UNRESOLVED FIELDS is non-empty, name them and say which columns are available instead - this is the only
  place you should push back.
- If ONTOLOGY TERMS is non-empty, list them as "code - label" so the user can check the mapping.
- If nothing was extracted, ask one concrete question that would move the query forward.
- Do not invent results, do not speculate about how many animals will match, do not add a conclusion.

QUERY ASKED BY USER
{query}

EXTRACTED (ignore if empty)
{extracted}

UNRESOLVED FIELDS (ignore if empty)
{unresolved}

ONTOLOGY TERMS (ignore if empty)
{terms}

OUTPUT
""",
        partial_variables=SCHEMA_PARTIAL,
    )

    return followup_template | llm_text


# --------------------------------------------------------------------------- #
# Analytics code generation
# --------------------------------------------------------------------------- #

analytics_code_generator_template = (
    DOMAIN_BACKGROUND
    + """
INSTRUCTIONS
Write python code that answers the user's query from the dataframes described below.
Comment the code so a non-programmer can follow it.
Respond in this JSON format:
{{
    "code": "python code",
    "files": [],        // output file paths written by the script
    "assumptions": [],  // short assumptions you made
    "feedback": []      // short notes for the user (never about imports or libraries)
}}

CONDITIONS
Only these libraries are available and they are ALREADY imported:
* Pandas (pd)  * Numpy (np)  * Matplotlib (plt)  * Seaborn (sns)
Do not write import statements. Do not simulate or fabricate data. Do not call plt.show(). Do not return anything.
Write every output file to /tmp/. Save figures with bbox_inches='tight'. Prefer vertical plot formats.
Do not check whether columns exist - the schema below is authoritative.
If a chosen field is a dict, it has keys "id" and "label"; if it is a list, its entries are such dicts.
Note that in each case, add a line to "feedback" so the user can adjust.

DOMAIN RULES FOR STATISTICS
- Allele frequency per SNP from calls: freq(B) = (2*BB + AB) / (2 * (AA + AB + BB)). NC rows must be excluded, not counted as 0.
- Major allele is whichever of A/B has frequency > 0.5; minor is the other. MAF = min(freq(A), freq(B)).
- Call rate = non-NC calls / total calls.
- Never average genotype strings; map them to dosages first.

INPUT
These pandas dataframes are available:
{data}

QUERY
{query}

OUTPUT
"""
)

analytics_table_data_template = """
Table name: {name}
    Columns: {cols}
    Datatypes: {types}
"""


def get_analytics_code_generator_chain():
    return get_extractor_chain(
        analytics_code_generator_template, GeneratedCodeAnalytics
    )


def generate_analytics_table_data(table_names, table_info):
    constructed_str = ""
    for name, (cols, types) in zip(table_names, table_info):
        constructed_str += analytics_table_data_template.format(
            name=name, cols=cols, types=types
        )
    return constructed_str


__all__ = [
    "get_validate_and_followup_chain",
    "get_data_extractor_map_chain",
    "get_success_followup_chain",
    "get_analytics_code_generator_chain",
    "generate_analytics_table_data",
    "get_extractor_chain",
    "extract_object",
]


if __name__ == "__main__":  # pragma: no cover - smoke check without an API key
    print(json.dumps(SCHEMA_PARTIAL, indent=2))
