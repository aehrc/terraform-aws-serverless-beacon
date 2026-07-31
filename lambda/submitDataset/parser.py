"""
Illumina report parser.

Fixes over the previous version, all confirmed against the supplied files:

* `coordinate` was coerced with float(), producing 5327353.0. Positions are
  integers - a float column breaks an Athena bigint and makes range predicates
  ("between position 1 and 50,000") lossy at large values.
* The genotype QC columns `r` and `log_r_ratio` were missing from the numeric
  set, so they landed in Athena as strings next to their double neighbours.
* The supplied phenotype file spells the column `weaing_weight_kg`. It was
  therefore in neither the numeric set nor any query - it is now canonicalised
  to `weaning_weight_kg` on ingest.
* Column names and types now come from shared.sheep_schema, so the parser, the
  validator and the prompts cannot drift apart again.
* Added a streaming entry point: the 21 MB genotype sample expands to ~200 MB
  of dicts, and a real multi-sample cohort file will be several times that.
"""

import re

from shared import sheep_schema

# Kept as module-level names for backwards compatibility with existing imports.
NUMERIC_FIELDS = sheep_schema.NUMERIC_FIELDS
INTEGER_FIELDS = sheep_schema.INTEGER_FIELDS

_CR = re.compile(r"\r")


def _coerce(key, value):
    value = value.strip() if isinstance(value, str) else value
    if key in INTEGER_FIELDS:
        try:
            # int("5327353.0") raises, so go via float for tolerance.
            return int(float(value))
        except (TypeError, ValueError):
            return None
    if key in NUMERIC_FIELDS:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    return value


def _parse_header(cols):
    keys = [sheep_schema.canonicalise_column(col) for col in cols]
    print(f"Found columns: {keys}")
    return keys


def iter_rows(lines, dataset_id, delimiter="\t", comment="#", route_type=None):
    """
    Yield one dict per data row.

    `lines` may be any iterable of strings - a file object, a list, or the
    result of splitting a string. Yielding keeps peak memory flat for the large
    genotype and manifest files.
    """
    keys = []
    bad_lines = 0

    for line_no, line in enumerate(lines, start=1):
        line = _CR.sub("", line).rstrip("\n")
        if not line or (comment and line.startswith(comment)):
            continue

        cols = line.split(delimiter)

        if not keys:
            keys = _parse_header(cols)
            if route_type is not None:
                allowed = set(sheep_schema.TABLE_COLUMNS[route_type])
                dropped = [k for k in keys if k not in allowed]
                if dropped:
                    # The Athena JSON schemas set additionalProperties:false, so
                    # extra provider columns must not be uploaded.
                    print(f"Dropping columns not in the {route_type} schema: {dropped}")
            continue

        if len(cols) != len(keys):
            bad_lines += 1
            if bad_lines <= 5:
                print(f"Warning: line {line_no} has {len(cols)} of {len(keys)} columns")
            continue

        entry = {"dataset_id": dataset_id}
        for key, value in zip(keys, cols):
            entry[key] = _coerce(key, value)
        yield sheep_schema.project_row(entry, route_type)

    if bad_lines:
        print(f"Skipped {bad_lines} malformed line(s)")


def extract(raw_input, dataset_id, delimiter="", comment="", route_type=None):
    """
    Backwards-compatible wrapper returning a list of dicts.

    Returns an empty list when nothing could be parsed, which callers already
    treat as a failure.
    """
    if not delimiter:
        delimiter = "\t"

    lines = raw_input.splitlines() if isinstance(raw_input, str) else raw_input
    extracted = list(iter_rows(lines, dataset_id, delimiter, comment, route_type))
    print(f"Successfully read file into {len(extracted)} rows")
    return extracted
