from datetime import datetime, timezone

import boto3
from pynamodb.models import Model
from pynamodb.settings import OperationSettings
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from pynamodb.attributes import (
    UnicodeAttribute,
    NumberAttribute,
    UnicodeSetAttribute,
    UTCDateTimeAttribute,
    ListAttribute,
    MapAttribute,
)

from utils.lambda_utils import ENV_DYNAMO


SESSION = boto3.session.Session()
REGION = SESSION.region_name


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
    chromosomes = UnicodeSetAttribute(default_for_new=[])


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
    datasetIndex = DatasetIndex()

    # overriding the method to add timestamp on update
    def update(self, actions=[], condition=None, settings=OperationSettings.default):
        actions.append(Dataset.updateDateTime.set(get_current_time_utc()))
        Model.update(self, actions, condition, settings)


if __name__ == "__main__":
    pass
