"""
Single source of truth for the AskTheSheeps (Illumina OvineSNP50) data model.

This module is deliberately dependency-free (stdlib only) so that BOTH layers
can import it:

  * the ingestion layer  -> parser.py, file_validator.py, route_create_dataset.py
    (these run in Lambdas that must not pull in langchain/openai)
  * the LLM layer        -> utils/models.py, utils/templates.py

Previously the column names lived in three places (parser.NUMERIC_FIELDS,
file_validator.REQUIRED_COLUMNS and the hand-written prompt text) and had
already drifted apart. Change a column here and every layer follows.
"""

# --------------------------------------------------------------------------- #
# Logical tables (matching shared.athena Snp / Sample / Genotype / Phenotype)
# --------------------------------------------------------------------------- #

SNP = "snp"
SAMPLE = "sample"
GENOTYPE = "genotype"
PHENOTYPE = "phenotype"

ROUTE_TYPES = (SNP, SAMPLE, GENOTYPE, PHENOTYPE)

# Every column we expect to see after parser.extract() has normalised headers
# (lower-cased, spaces/dashes -> underscore, aliases applied).
TABLE_COLUMNS = {
    # Exactly the columns snp-schema.json declares. That schema sets
    # additionalProperties:false, so anything else in the manifest is a
    # validation failure and must not be uploaded.
    SNP: [
        "dataset_id",
        "id",
        "chromosome",
        "coordinate",
        "allelea_top_base",
        "alleleb_top_base",
    ],
    SAMPLE: [
        "dataset_id",
        "sample_id",
        "breed",
        "sex",
    ],
    # Exactly the columns genotype-schema.json declares.
    GENOTYPE: [
        "dataset_id",
        "sample_id",
        "id_ref",
        "value",
        "score",
        "theta",
        "b_allele_freq",
    ],
    PHENOTYPE: [
        "dataset_id",
        "sample_id",
        "sex",
        "birth_weight_kg",
        "weaning_weight_kg",
        "six_month_weight_kg",
        "fat_thickness_cm",
        "eye_muscle_area_cm2",
        "height_at_withers_cm",
        "chest_girth_cm",
        "shin_circumference_cm",
        "pre_weaning_gain_kg",
        "post_weaning_gain_kg",
        "daily_weight_gain_kg",
    ],
}

KNOWN_UNUSED_COLUMNS = {
    # Columns the provider files contain that the Athena JSON schemas do not
    # declare. Listed explicitly so the decision stays visible - requirements
    # 1.5 notes a report "usually has more columns than these, but these are the
    # columns producers are interested in". To keep one of these, add it to the
    # JSON schema AND to TABLE_COLUMNS above.
    SNP: [
        "genomebuild",
        "top_genomic_sequence",
        "forward_sequence",
        "allelea_forward",
        "alleleb_forward",
        "spot_id",
    ],
    GENOTYPE: ["r", "log_r_ratio"],
    SAMPLE: [],
    PHENOTYPE: [],
}


def project_row(row, route_type):
    """Drop any column the table's JSON schema does not declare."""
    if route_type is None:
        return row
    allowed = TABLE_COLUMNS[route_type]
    return {key: row[key] for key in allowed if key in row}


# --------------------------------------------------------------------------- #
# Typing
# --------------------------------------------------------------------------- #

# Genomic coordinates are integers. The old parser coerced them with float(),
# which produced 5327353.0 and (a) breaks an Athena bigint column and
# (b) makes "between position 1 and 50,000" comparisons lossy for large values.
INTEGER_FIELDS = {"coordinate"}

FLOAT_FIELDS = {
    # genotype QC metrics, all declared "number" in genotype-schema.json
    "score",
    "theta",
    "b_allele_freq",
    # phenotype measurements
    "birth_weight_kg",
    "weaning_weight_kg",
    "six_month_weight_kg",
    "fat_thickness_cm",
    "eye_muscle_area_cm2",
    "height_at_withers_cm",
    "chest_girth_cm",
    "shin_circumference_cm",
    "pre_weaning_gain_kg",
    "post_weaning_gain_kg",
    "daily_weight_gain_kg",
}

NUMERIC_FIELDS = INTEGER_FIELDS | FLOAT_FIELDS

VALID_GENOTYPE_CALLS = ("AA", "AB", "BB", "NC")

# The OvineSNP50 manifest reports "GenomeBuild = draft genome build 1" rather
# than a named assembly. Beacon still requires an assemblyId, and it is the hash
# key of the datasets assembly_index GSI, so the ingestion route, the Dataset
# row and the query layer must all use the same string or the lookup silently
# returns nothing. Defined here because this module has no third-party imports;
# shared/dynamodb/datasets.py re-exports it as DEFAULT_OVINE_ASSEMBLY_ID.
DEFAULT_ASSEMBLY_ID = "OARv3.1"

# Chromosome values actually present in the OvineSNP50 manifest: 1-26, X, Y,
# plus "0" (unmapped), "OAR" (OARUn unplaced scaffolds) and "Contig".
AUTOSOMES = [str(i) for i in range(1, 27)]
VALID_CHROMOSOMES = set(AUTOSOMES) | {"X", "Y", "0", "OAR", "Contig"}

# --------------------------------------------------------------------------- #
# Header canonicalisation (applied at ingest time by parser.extract)
# --------------------------------------------------------------------------- #

# Providers do not agree on header spelling, and one of the supplied files has a
# genuine typo ("weaing_weight_kg"). Canonicalise on the way in so the Athena
# columns are stable and the LLM never has to guess a misspelling.
#
# NOTE: shared/athena Phenotype must declare `weaning_weight_kg` (not
# `weaing_weight_kg`) for this to line up. That is the one schema edit this
# change requires.
COLUMN_ALIASES = {
    "sample_name": "sample_id",
    "sample name": "sample_id",
    "weaing_weight_kg": "weaning_weight_kg",
    "wean_weight_kg": "weaning_weight_kg",
    "snp_name": "id",
    "snp_id": "id",
    "gtype": "value",
    "genotype": "value",
    "map_info": "coordinate",
    "mapinfo": "coordinate",
    "position": "coordinate",
    "chr": "chromosome",
}


def canonicalise_column(name: str) -> str:
    """Normalise a raw header cell to its canonical column name."""
    key = name.strip().lower().replace(" ", "_").replace("-", "_")
    return COLUMN_ALIASES.get(key, key)


# --------------------------------------------------------------------------- #
# Natural-language field resolution (used by the LLM layer)
# --------------------------------------------------------------------------- #

# Maps what a producer is likely to say -> the real column name. Applied AFTER
# the LLM has extracted a filter, so a wording slip does not become a silently
# broken Athena predicate.
NL_FIELD_ALIASES = {
    "birth_weight": "birth_weight_kg",
    "birthweight": "birth_weight_kg",
    "weight_at_birth": "birth_weight_kg",
    "weaning_weight": "weaning_weight_kg",
    "weaing_weight_kg": "weaning_weight_kg",
    "six_month_weight": "six_month_weight_kg",
    "fat_thickness": "fat_thickness_cm",
    "eye_muscle_area": "eye_muscle_area_cm2",
    "emd": "eye_muscle_area_cm2",
    "height": "height_at_withers_cm",
    "height_at_withers": "height_at_withers_cm",
    "chest_girth": "chest_girth_cm",
    "shin_circumference": "shin_circumference_cm",
    "daily_gain": "daily_weight_gain_kg",
    "adg": "daily_weight_gain_kg",
    "gender": "sex",
    "animal_id": "sample_id",
    "sample": "sample_id",
    "snp": "id",
    "snp_name": "id",
    "marker": "id",
    "call": "value",
    "genotype_call": "value",
    "bp": "coordinate",
    "base_pair": "coordinate",
    "location": "coordinate",
    "call_rate": "score",
    "gc_score": "score",
}

# Flat lookup: column -> table it belongs to (first match wins; sample_id, sex
# and dataset_id legitimately appear in more than one table).
_FIELD_TABLE = {}
for _table in (SNP, SAMPLE, GENOTYPE, PHENOTYPE):
    for _col in TABLE_COLUMNS[_table]:
        _FIELD_TABLE.setdefault(_col, _table)

ALL_FIELDS = set(_FIELD_TABLE)


def resolve_field(name):
    """
    Resolve a field name produced by the LLM to a real column.

    Returns the canonical column name, or None when it cannot be resolved -
    callers should surface that to the user rather than sending an invented
    column to Athena.
    """
    if not name:
        return None
    key = str(name).strip().lower().replace(" ", "_").replace("-", "_")
    key = COLUMN_ALIASES.get(key, key)
    key = NL_FIELD_ALIASES.get(key, key)
    return key if key in ALL_FIELDS else None


def field_table(name):
    """Which logical table a resolved column lives in."""
    return _FIELD_TABLE.get(name)


def is_numeric_field(name) -> bool:
    return name in NUMERIC_FIELDS


def describe_schema() -> str:
    """Human/LLM readable schema block, injected into the prompts."""
    lines = []
    for table in (SNP, SAMPLE, GENOTYPE, PHENOTYPE):
        cols = [c for c in TABLE_COLUMNS[table] if c != "dataset_id"]
        annotated = [f"{c} (num)" if c in NUMERIC_FIELDS else c for c in cols]
        lines.append(f"{table}: {', '.join(annotated)}")
    return "\n".join(lines)
