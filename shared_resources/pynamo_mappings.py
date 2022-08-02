import os
from pynamodb.models import Model
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection, IncludeProjection
from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute, UnicodeSetAttribute, UTCDateTimeAttribute, ListAttribute, MapAttribute
)

DATASETS_TABLE_NAME = os.environ['DATASETS_TABLE']


# Dataset index
class DatasetIndex(GlobalSecondaryIndex):
    """
    This class represents a global secondary index
    """
    class Meta:
        index_name = 'assembly_index'
        projection = AllProjection()
        billing_mode = "PAY_PER_REQUEST"

    assemblyId = UnicodeAttribute(hash_key=True)
    id = UnicodeAttribute()
    vcfGroups = ListAttribute(of=UnicodeSetAttribute)
    vcfLocations = UnicodeSetAttribute()


# dataset table
class Dataset(Model):
    class Meta:
        table_name = DATASETS_TABLE_NAME

    id = UnicodeAttribute(hash_key=True)
    assemblyId = UnicodeAttribute()
    name = UnicodeAttribute()
    sampleCount = NumberAttribute()
    callCount = NumberAttribute()
    createDateTime = UTCDateTimeAttribute()
    updateDateTime = UTCDateTimeAttribute()
    variantCount = NumberAttribute()
    vcfGroups = ListAttribute(of=UnicodeSetAttribute)
    vcfLocations = UnicodeSetAttribute()
    datasetIndex = DatasetIndex()


if __name__ == '__main__':
    for item in Dataset.datasetIndex.query('MTD-1'):
        for loc in item.vcfLocations:
            print(loc)
    item = Dataset.get('test-wic')
    print(item.assemblyId)