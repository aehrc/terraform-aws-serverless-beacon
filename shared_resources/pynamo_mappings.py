from email.policy import default
import os
from datetime import datetime, timezone
from pydoc import describe
import time

from pynamodb.models import Model
from pynamodb.settings import OperationSettings
from pynamodb.indexes import GlobalSecondaryIndex, LocalSecondaryIndex, AllProjection
from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute, UnicodeSetAttribute, UTCDateTimeAttribute, ListAttribute, MapAttribute
)

DATASETS_TABLE_NAME = os.environ['DATASETS_TABLE']
QUERIES_TABLE_NAME = os.environ['QUERIES_TABLE']
VARIANT_QUERY_RESPONSES_TABLE_NAME = os.environ['VARIANT_QUERY_RESPONSES_TABLE']


def get_current_time_utc():
        return datetime.now(timezone.utc)


class S3Location(MapAttribute):
    bucket = UnicodeAttribute()
    key = UnicodeAttribute()

# Datasets index
class DatasetIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = 'assembly_index'
        projection = AllProjection()
        billing_mode = "PAY_PER_REQUEST"

    assemblyId = UnicodeAttribute(hash_key=True)


# datasets table
class Dataset(Model):
    class Meta:
        table_name = DATASETS_TABLE_NAME

    id = UnicodeAttribute(hash_key=True)
    assemblyId = UnicodeAttribute()
    name = UnicodeAttribute()
    description = UnicodeAttribute(default='')
    version = UnicodeAttribute(default='')
    externalUrl = UnicodeAttribute(default='')
    info = ListAttribute(of=UnicodeAttribute, default=list)
    dataUseConditions = MapAttribute(default={})
    sampleCount = NumberAttribute(default=0)
    callCount = NumberAttribute(default=0)
    createDateTime = UTCDateTimeAttribute(default_for_new=get_current_time_utc)
    updateDateTime = UTCDateTimeAttribute(default_for_new=get_current_time_utc)
    variantCount = NumberAttribute(default=0)
    vcfGroups = ListAttribute(of=UnicodeSetAttribute, default=list)
    vcfLocations = UnicodeSetAttribute(default=set)
    datasetIndex = DatasetIndex()


    # overriding the method to add timestamp on update
    def update(self, actions=[], condition=None, settings=OperationSettings.default):
        actions.append(Dataset.updateDateTime.set(get_current_time_utc()))
        Model.update(self, actions, condition, settings)


# queries table
class VariantQuery(Model):
    class Meta:
        table_name = QUERIES_TABLE_NAME

    id = UnicodeAttribute(hash_key=True, default='test')
    responsesCounter = NumberAttribute(default=0)
    responses = NumberAttribute(default=0)
    fanOut = NumberAttribute(default=0)


    # atomically increment
    def getResponseNumber(self):
        self.update(actions=[
            VariantQuery.responsesCounter.set(VariantQuery.responsesCounter + 1),
        ])
        return self.responsesCounter


    # atomically increment
    def markFinished(self):
        self.update(actions=[
            VariantQuery.responses.set(VariantQuery.responses + 1),
            VariantQuery.fanOut.set(VariantQuery.fanOut - 1),
        ])


class VariantResponseIndex(LocalSecondaryIndex):
    class Meta:
        index_name = 'responseNumber_index'
        projection = AllProjection()
        billing_mode = "PAY_PER_REQUEST"

    id = UnicodeAttribute(hash_key=True)
    responseNumber = NumberAttribute(range_key=True)


# query responses table
class VariantResponse(Model):
    class Meta:
        table_name = VARIANT_QUERY_RESPONSES_TABLE_NAME

    id = UnicodeAttribute(hash_key=True, default='test')
    responseNumber = NumberAttribute(default=0)
    responseLocation = S3Location()
    variantResponseIndex = VariantResponseIndex()


if __name__ == '__main__':
    # these are tests
    # for item in Dataset.datasetIndex.query('MTD-1'):
    #     for loc in item.vcfLocations:
    #         print(loc)
    # item = Dataset.get('test-wic')
    # print(item.assemblyId)

    # d = Dataset('pynamodb-test')
    # d.assemblyId = 'pynamodb-assembly-id-test'
    # d.name = 'pynamodb-name-test'
    # d.sampleCount = 100
    # d.callCount = 99
    # d.variantCount = 999
    # d.vcfGroups = list()
    # d.vcfGroups.append(['vcf1', 'vcf2'])
    # d.vcfGroups.append(['vcf3'])
    # d.vcfLocations = set()
    # d.vcfLocations.add('vcf1')
    # d.vcfLocations.add('vcf2')
    # d.vcfLocations.add('vcf3')
    # d.save()

    # e = Dataset.get('pynamodb-test')
    # print('e.callCount ', e.callCount)
    # print('e.updateDateTime ', e.updateDateTime)
    # time.sleep(2)
    # e.update(actions=[
    #     Dataset.callCount.set(e.callCount + 1),
    #     # Dataset.updateDateTime.set(get_current_time_utc())
    # ])
    # print('e.callCount ', e.callCount)
    # print('e.updateDateTime ', e.updateDateTime)

    # time.sleep(2)

    # Dataset('pynamodb-test').update(actions=[
    #     Dataset.callCount.set(165),
    # ])
    # f = Dataset.get('pynamodb-test')
    # print('f.callCount ', f.callCount)
    # print('f.updateDateTime ', f.updateDateTime)

    q = VariantQuery()
    q.save()

    print(q.id, q.responses)
    q.markFinished()
    print(q.id, q.responses)

    vr = VariantResponse()
    rl = S3Location()
    rl.bucket = 'mybucket'
    rl.key = 'mykey'
    vr.responseLocation = rl
    vr.save()
