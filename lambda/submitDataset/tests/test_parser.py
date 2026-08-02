# Test cases for extract

from submitDataset.parser import extract

def test_extract_sample():
    raw = "sample_id,breed,sex\n1,Merino,male\n2,Dorset,female"

    rows = extract(raw, "sample1", delimiter=",")

    assert rows == [
        {"dataset_id": "sample1", "sample_id": "1", "breed": "Merino", "sex": "male"},
        {"dataset_id": "sample1", "sample_id": "2", "breed": "Dorset", "sex": "female"},
    ]

def test_extract_genotype_txt():
    raw = ("id_ref\tvalue\tscore\ttheta\tb_allele_freq\n"
        "rs1\tAA\t0.95\t0.42\t0.12\n"
        "rs2\tAB\t0.87\t0.51\t0.48"
    )

    rows = extract(raw, "genotype1", delimiter="\t")

    assert rows == [
        {
            "dataset_id": "genotype1",
            "id_ref": "rs1",
            "value": "AA",
            "score": 0.95,
            "theta": 0.42,
            "b_allele_freq": 0.12,
        },
        {
            "dataset_id": "genotype1",
            "id_ref": "rs2",
            "value": "AB",
            "score": 0.87,
            "theta": 0.51,
            "b_allele_freq": 0.48,
        },
    ]

def test_extract_snp_txt():
    raw = (
        "id\tchromosome\tcoordinate\tallelea_top_base\talleleb_top_base\n"
        "rs1\t1\t12345\tA\tG\n"
        "rs2\t2\t67890\tC\tT"
    )

    rows = extract(raw, "snp1", delimiter="\t")

    assert rows == [
        {
            "dataset_id": "snp1",
            "id": "rs1",
            "chromosome": "1",
            "coordinate": 12345,
            "allelea_top_base": "A",
            "alleleb_top_base": "G",
        },
        {
            "dataset_id": "snp1",
            "id": "rs2",
            "chromosome": "2",
            "coordinate": 67890,
            "allelea_top_base": "C",
            "alleleb_top_base": "T",
        },
    ]

def test_extract_phenotype():
    raw = "sample_id,sex,birth_weight_kg\nmerino1,male,3\nmerino2,female,2"

    rows = extract(raw, "phenotype1", delimiter=",")

    assert rows == [
        {"dataset_id": "phenotype1", "sample_id": "merino1", "sex": "male", "birth_weight_kg": 3},
        {"dataset_id": "phenotype1", "sample_id": "merino2", "sex": "female", "birth_weight_kg": 2},
    ]

if __name__ == "__main__":

    tests = [test_extract_sample, test_extract_genotype_txt, test_extract_snp_txt, test_extract_phenotype]

    for test in tests:
        try:
            test()
            print(f"Pass: {test.__name__}")
        except AssertionError as e:
            print(f"Fail {test.__name__}: {e}")
            raise

    print("\nAll tests passed")
