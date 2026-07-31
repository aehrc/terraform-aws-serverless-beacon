"""
shared/dynamodb/datasets.py

WHAT THIS FILE DOES
-------------------
It defines the DynamoDB models for the sBeacon `datasets` DynamoDB table -
the registry of every dataset the Beacon knows about. One row per dataset.
Everything downstream resolves a dataset through this row: the `/datasets`
Beacon endpoint lists them, the variant query lambdas look up which files to
scan, and the `assembly_index` GSI is how a `/g_variants` request narrows to the
datasets built on a given assembly.

Nothing in the original file is removed. Three attributes and one MapAttribute
are added so an Illumina array dataset can be registered in the same table as a
VCF dataset, which is what "ingest OvineSNP50 data without VCF conversion"
requires - the row is what makes a dataset queryable at all.

WHAT WAS ADDED AND WHY
----------------------
dataType          "vcf" | "illumina". Declared null=True with
                  default_for_new="vcf", so the ~existing rows in a deployed
                  table (which have no such attribute) still deserialise and
                  still read as VCF. This is the field the frontend toggle and
                  the query router branch on.
illuminaLocations The S3 URIs of the four report files. VCF datasets keep using
                  vcfLocations; the two never collide.
hasPhenotypes     Whether an optional phenotype file was supplied. Lets the
                  query layer refuse a phenotype filter up front instead of
                  returning an empty result set.

Existing attributes are reused rather than duplicated, to keep the Beacon
`/datasets` response meaningful for both data types:

    sampleNames   -> sample_id values from samples.csv
    sampleCount   -> number of animals
    variantCount  -> number of SNPs in the manifest
    callCount     -> number of genotype rows ingested

assemblyId is NOT optional in this model (an AttributeNullError is raised on
save without it) and it is the GSI hash key, so an Illumina dataset must record
one. The OvineSNP50 manifest is not on a human assembly, hence
DEFAULT_OVINE_ASSEMBLY_ID below. Whatever is stored here has to match the
assemblyId the query layer sends, or the GSI lookup returns nothing.
"""

from datetime import datetime, timezone

import boto3
from pynamodb.attributes import (
    BooleanAttribute,
    ListAttribute,
    MapAttribute,
    NumberAttribute,
    UnicodeAttribute,
    UnicodeSetAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.indexes import AllProjection, GlobalSecondaryIndex
from pynamodb.models import Model
from shared.sheep_schema import DEFAULT_ASSEMBLY_ID
from shared.utils import ENV_DYNAMO

SESSION = boto3.session.Session()
REGION = SESSION.region_name

# Data types
DATA_TYPE_VCF = "vcf"
DATA_TYPE_ILLUMINA = "illumina"

# Re-exported from shared/sheep_schema.py so the ingestion route, this row and
# the query layer cannot drift apart.
DEFAULT_OVINE_ASSEMBLY_ID = DEFAULT_ASSEMBLY_ID


def get_current_time_utc():
    return datetime.now(timezone.utc)


# Datasets index
class DatasetIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = "assembly_index"
        projection = AllProjection()
        billing_mode = "PAY_PER_REQUEST"
        region = REGION

    assemblyId = UnicodeAttribute(hash_key=True)


class VcfChromosomeMap(MapAttribute):
    vcf = UnicodeAttribute()
    chromosomes = UnicodeSetAttribute(default_for_new=list)


class IlluminaLocations(MapAttribute):
    """
    S3 URIs of the files that make up one Illumina genotyping report.

    snp and sample are single files; a report can be split across several
    genotype files, and phenotypes are optional (see requirements 1.5).
    """

    snp = UnicodeAttribute(null=True)
    sample = UnicodeAttribute(null=True)
    genotypes = ListAttribute(of=UnicodeAttribute, default=list)
    phenotypes = ListAttribute(of=UnicodeAttribute, default=list)


# datasets table
class Dataset(Model):
    class Meta:
        table_name = ENV_DYNAMO.DYNAMO_DATASETS_TABLE
        region = REGION

    id = UnicodeAttribute(hash_key=True)
    assemblyId = UnicodeAttribute()
    sampleCount = NumberAttribute(null=True, default=None)
    sampleNames = UnicodeSetAttribute(default=set)
    callCount = NumberAttribute(null=True, default=None)
    createDateTime = UTCDateTimeAttribute(default_for_new=get_current_time_utc)
    updateDateTime = UTCDateTimeAttribute(default_for_new=get_current_time_utc)
    variantCount = NumberAttribute(null=True, default=None)
    vcfGroups = ListAttribute(of=UnicodeSetAttribute, default=list)
    vcfLocations = UnicodeSetAttribute(default=set)
    vcfChromosomeMap = ListAttribute(of=VcfChromosomeMap, default=list)

    # --- Illumina native ingestion -------------------------------------- #
    dataType = UnicodeAttribute(null=True, default_for_new=DATA_TYPE_VCF)
    illuminaLocations = IlluminaLocations(null=True)
    hasPhenotypes = BooleanAttribute(null=True, default_for_new=False)
    # -------------------------------------------------------------------- #

    datasetIndex = DatasetIndex()

    @property
    def is_illumina(self) -> bool:
        """Rows written before this change have no dataType; treat them as VCF."""
        return (self.dataType or DATA_TYPE_VCF) == DATA_TYPE_ILLUMINA

    # overriding the method to add timestamp on update
    def update(self, actions=[], condition=None):
        actions.append(Dataset.updateDateTime.set(get_current_time_utc()))
        Model.update(self, actions, condition)


if __name__ == "__main__":
    pass
