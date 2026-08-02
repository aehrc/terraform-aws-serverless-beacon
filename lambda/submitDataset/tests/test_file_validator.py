# Test cases for file_validator.py

from submitDataset.file_validator import validate_file, validate_req_cols, validate_rows

def test_missing_req_cols():
    rows= [{"breed": "Sunit"}]
    error = validate_req_cols("sample", rows)
    assert error == "Missing required columns: ['sample_id', 'sex']"

    rows = [{"id": "rs123", "chromosome": "1", "coordinate": 12345, "allelea_top_base": "A"}]
    error = validate_req_cols("snp", rows)
    assert error == "Missing required columns: ['alleleb_top_base']"

    rows = [{"value": "AA", "id_ref": "rs123"}]
    error = validate_req_cols("genotype", rows)
    assert error == "Missing required columns: ['sample_id']"

    # Test that missing columns are prioritised over missing values in rows
    rows = [{"value": "DD", "id_ref": "", "ref_allele": "T"}]
    error = validate_req_cols("genotype", rows)
    assert error == "Missing required columns: ['sample_id']"


def test_validate_req_cols_valid():
    rows = [{"sample_id": "123", "breed": "Sunit", "sex": "Female"}]
    assert validate_req_cols("sample", rows) is None


def test_validate_rows():
    rows = [{"sample_id": "123", "value": "AC", "id_ref": "rs123"}]
    error = validate_rows("genotype", rows)
    assert error == "Validation errors - invalid rows: Invalid genotype value in one or more rows (expected 'AA', 'AB', 'BB', or 'NC')."

    rows = [{"sample_id": "123", "value": "AA", "id_ref": None}]
    error = validate_rows("genotype", rows)
    assert error == "Validation errors - invalid rows: Missing required SNP ID in one or more rows."


def test_validate_rows_multiple_rows():
    # Row has invalid genotype value
    rows = [
        {"sample_id": "123", "value": "AA", "id_ref": "rs123"},
        {"sample_id": "456", "value": "XX", "id_ref": "rs456"},
        {"sample_id": "789", "value": "BB", "id_ref": "rs789"},
    ]

    error = validate_rows("genotype", rows)

    assert error == ("Validation errors - invalid rows: Invalid genotype value in one or more rows (expected 'AA', 'AB', 'BB', or 'NC').")


def test_validate_rows_multiple_missing_ids():
    rows = [
        {"sample_id": "123", "value": "AA", "id_ref": None},
        {"sample_id": "456", "value": "AB", "id_ref": ""},
        {"sample_id": "789", "value": "BB", "id_ref": "rs789"},
    ]

    error = validate_rows("genotype", rows)

    assert error == ("Validation errors - invalid rows: Missing required SNP ID in one or more rows.")


def test_validate_rows_multiple_errors():
    rows = [
        {"sample_id": "123", "value": "AC", "id_ref": None},
        {"sample_id": "456", "value": "ZZ", "id_ref": "rs456"},
        {"sample_id": "789", "value": "AA", "id_ref": "rs789"},
    ]

    error = validate_rows("genotype", rows)

    assert error == ("Validation errors - invalid rows: Missing required SNP ID in one or more rows. Invalid genotype value in one or more rows (expected 'AA', 'AB', 'BB', or 'NC').")

if __name__ == "__main__":
    
    tests = [test_missing_req_cols, test_validate_req_cols_valid, test_validate_rows, test_validate_rows_multiple_rows, test_validate_rows_multiple_missing_ids, test_validate_rows_multiple_errors]

    for test in tests:
        try:
            test()
            print(f"Pass: {test.__name__}")
        except AssertionError as e:
            print(f"Fail {test.__name__}: {e}")
            raise

    print("\nAll tests passed")
