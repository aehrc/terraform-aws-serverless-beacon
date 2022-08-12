from email.policy import default
import os
from datetime import datetime, timezone

from pynamodb.models import Model
from pynamodb.indexes import LocalSecondaryIndex, AllProjection
from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute, MapAttribute
)


QUERIES_TABLE_NAME = os.environ['QUERIES_TABLE']
VARIANT_QUERY_RESPONSES_TABLE_NAME = os.environ['VARIANT_QUERY_RESPONSES_TABLE']


def get_current_time_utc():
        return datetime.now(timezone.utc)


class S3Location(MapAttribute):
    bucket = UnicodeAttribute()
    key = UnicodeAttribute()


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
