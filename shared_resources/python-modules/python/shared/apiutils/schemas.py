#
# Start Thirdparty Code
# Code from https://github.com/EGA-archive/beacon2-ri-api
# Apache License 2.0
#

from enum import Enum


class DefaultSchemas(Enum):
    ANALYSES = {"entityType": "analysis", "schema": "beacon-analysis-v2.0.0"}
    BIOSAMPLES = {"entityType": "biosample", "schema": "beacon-dataset-v2.0.0"}
    COHORTS = {"entityType": "cohort", "schema": "beacon-cohort-v2.0.0"}
    DATASETS = {"entityType": "dataset", "schema": "beacon-dataset-v2.0.0"}
    GENOMICVARIATIONS = {
        "entityType": "genomicVariation",
        "schema": "beacon-g_variant-v2.0.0",
    }
    INDIVIDUALS = {"entityType": "individual", "schema": "beacon-individual-v2.0.0"}
    RUNS = {"entityType": "run", "schema": "beacon-run-v2.0.0"}
    SAMPLES = {"entityType": "sample", "schema": "beacon-sample-v2.0.0"}
    GENOTYPES = {"entityType": "genotype", "schema": "beacon-genotype-v2.0.0"}
    SNPS = {"entityType": "snp", "schema": "beacon-snp-v2.0.0"}
    PHENOTYPES = {"entityType": "phenotype", "schema": "beacon-phenotype-v2.0.0"}


#
# End Thirdparty Code
#
