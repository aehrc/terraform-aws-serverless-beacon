from shared.sheep_schema import (
    NUMERIC_FIELDS,
    VALID_CHROMOSOMES,
    VALID_GENOTYPE_CALLS,
)

# Unchanged from the original - kept here rather than moved into sheep_schema so
# that anything already importing file_validator.REQUIRED_COLUMNS keeps working.
REQUIRED_COLUMNS = {
    "sample": {
        "sample_id",
        "breed",
        "sex",
    },
    "snp": {
        "id",
        "chromosome",
        "coordinate",
        "allelea_top_base",
        "alleleb_top_base",
    },
    "genotype": {
        "id_ref",
        "value",
        "sample_id"
    },
    "phenotype": {
        "sample_id"
    }
}

SNP_ID = ["snp", "genotype"]
SAMPLE_ID = ["sample", "genotype", "phenotype"]

# Cap on how many offending row numbers are listed in an error message.
MAX_REPORTED = 5


def validate_file(route_type, rows):
    """ Validate that the contents of a given file (rows) match expected format of given route_type"""

    col_error = validate_req_cols(route_type, rows)
    if col_error:
        return col_error

    return validate_rows(route_type, rows)


def validate_req_cols(route_type, rows):
    """ Validate that the contents of a given file (rows) contain the required columns for the given route_type"""
    if not rows:
        return "File is empty."

    req_cols = REQUIRED_COLUMNS.get(route_type, set())
    missing_cols = req_cols - set(rows[0].keys())

    if missing_cols:
        missing_cols = list(missing_cols)
        print(f"Validation errors - missing columns: {missing_cols}")
        # CHANGED: also list what was found, so a header or delimiter mistake is
        # obvious from the API response instead of needing the Lambda logs.
        found = sorted(k for k in rows[0] if k != "dataset_id")
        return f"Missing required columns: {sorted(missing_cols)}. Found: {found}"

    return None


def _report(label, rows_hit):
    """CHANGED: name the offending rows instead of saying 'one or more rows'."""
    shown = ", ".join(str(r) for r in rows_hit[:MAX_REPORTED])
    extra = len(rows_hit) - MAX_REPORTED
    more = f" (+{extra} more)" if extra > 0 else ""
    return f"{label} at row(s) {shown}{more}."


def validate_rows(route_type, rows):
    """ Validate that the rows have the correct format for the given route_type"""
    errors = []
    missing_snp_ids = []
    missing_sample_ids = []
    bad_calls = []
    bad_chromosomes = []
    bad_numerics = []

    # Only check the numeric columns this file actually has.
    numeric_cols = [col for col in rows[0] if col in NUMERIC_FIELDS]

    for index, row in enumerate(rows, start=1):
        if route_type in SNP_ID and not (row.get("id") or row.get("id_ref")):
            missing_snp_ids.append(index)

        if route_type in SAMPLE_ID and not row.get("sample_id"):
            missing_sample_ids.append(index)

        if route_type == "genotype" and row.get("value") not in VALID_GENOTYPE_CALLS:
            bad_calls.append(index)

        # CHANGED: the manifest legitimately uses 0, X, Y, OAR and Contig as well
        # as 1-26 (63 OAR rows and 313 at chromosome 0 in the supplied file), so
        # this accepts those and rejects anything else.
        if route_type == "snp" and str(row.get("chromosome")) not in VALID_CHROMOSOMES:
            bad_chromosomes.append(index)

        # CHANGED: a string in a numeric column used to upload cleanly and only
        # fail much later, at query time, as an Athena type error.
        for col in numeric_cols:
            value = row.get(col)
            if value is not None and not isinstance(value, (int, float)):
                bad_numerics.append(index)
                break

    if missing_snp_ids:
        errors.append(_report("Missing required SNP ID", missing_snp_ids))
    if missing_sample_ids:
        errors.append(_report("Missing required sample_id", missing_sample_ids))
    if bad_calls:
        errors.append(
            _report(
                "Invalid genotype value (expected 'AA', 'AB', 'BB', or 'NC')", bad_calls
            )
        )
    if bad_chromosomes:
        errors.append(_report("Unrecognised chromosome value", bad_chromosomes))
    if bad_numerics:
        errors.append(_report("Non-numeric value in a numeric column", bad_numerics))

    if errors:
        print(f"Validation errors - invalid rows: {' '.join(errors)}")
        return f"Validation errors - invalid rows: {' '.join(errors)}"

    return None


def validate_cross_file(snp_rows, sample_rows, genotype_rows, phenotype_rows=None):
    """
    NEW, optional: check that the files agree with each other.

    Each file can be individually valid while describing a different cohort. A
    genotype file whose sample_ids are absent from samples.csv uploads cleanly
    and then every query silently returns nothing, which is very hard to debug
    after the fact.

    Returns an error string, or None when the files are consistent.
    """
    errors = []
    snp_ids = {row.get("id") for row in snp_rows}
    sample_ids = {row.get("sample_id") for row in sample_rows}

    unknown_samples = {
        row.get("sample_id")
        for row in genotype_rows
        if row.get("sample_id") not in sample_ids
    }
    if unknown_samples:
        listed = ", ".join(sorted(str(s) for s in unknown_samples)[:MAX_REPORTED])
        errors.append(
            f"Genotype file references {len(unknown_samples)} sample(s) missing from the sample file: {listed}."
        )

    unknown_snps = {
        row.get("id_ref") for row in genotype_rows if row.get("id_ref") not in snp_ids
    }
    if unknown_snps:
        listed = ", ".join(sorted(str(s) for s in unknown_snps)[:MAX_REPORTED])
        errors.append(
            f"Genotype file references {len(unknown_snps)} marker(s) missing from the SNP manifest: {listed}."
        )

    for row in phenotype_rows or []:
        if row.get("sample_id") not in sample_ids:
            errors.append(
                f"Phenotype file references unknown sample_id '{row.get('sample_id')}'."
            )
            break

    return " ".join(errors) if errors else None
