from datetime import datetime, timezone, timedelta
from enum import Enum

import boto3
from pynamodb.models import Model
from pynamodb.indexes import LocalSecondaryIndex, AllProjection
from pynamodb.attributes import (
    UnicodeAttribute,
    NumberAttribute,
    MapAttribute,
    TTLAttribute,
    BooleanAttribute,
    UTCDateTimeAttribute,
)

from shared.utils import ENV_DYNAMO


SESSION = boto3.session.Session()
REGION = SESSION.region_name


def get_current_time_utc():
    return datetime.now(timezone.utc)


class S3Location(MapAttribute):
    bucket = UnicodeAttribute()
    key = UnicodeAttribute()


# queries table
class VariantQuery(Model):
    class Meta:
        table_name = ENV_DYNAMO.DYNAMO_VARIANT_QUERIES_TABLE
        region = REGION

    id = UnicodeAttribute(hash_key=True, default="test")
    responsesCounter = NumberAttribute(default=0)
    responses = NumberAttribute(default=0)
    fanOut = NumberAttribute(default=0)
    startTime = UTCDateTimeAttribute(default_for_new=get_current_time_utc())
    endTime = UTCDateTimeAttribute(null=True)
    elapsedTime = NumberAttribute(default_for_new=-1)
    timeToExist = TTLAttribute(default_for_new=timedelta(minutes=5))
    complete = BooleanAttribute(default_for_new=False)

    # atomically increment
    def getResponseNumber(self):
        self.update(
            actions=[
                VariantQuery.responsesCounter.set(VariantQuery.responsesCounter + 1),
            ]
        )
        return self.responsesCounter

    # atomically increment
    def markFinished(self):
        self.update(
            actions=[
                VariantQuery.responses.set(VariantQuery.responses + 1),
                VariantQuery.fanOut.set(VariantQuery.fanOut - 1),
                VariantQuery.endTime.set(get_current_time_utc()),
            ]
        )


class VariantResponseIndex(LocalSecondaryIndex):
    class Meta:
        index_name = "responseNumber_index"
        projection = AllProjection()
        billing_mode = "PAY_PER_REQUEST"
        region = REGION

    id = UnicodeAttribute(hash_key=True)
    responseNumber = NumberAttribute(range_key=True)


# query responses table
class VariantResponse(Model):
    class Meta:
        table_name = ENV_DYNAMO.DYNAMO_VARIANT_QUERY_RESPONSES_TABLE
        region = REGION

    id = UnicodeAttribute(hash_key=True, default="test")
    responseNumber = NumberAttribute(range_key=True, default=0)
    responseLocation = S3Location(null=True)
    variantResponseIndex = VariantResponseIndex()
    checkS3 = BooleanAttribute()
    result = UnicodeAttribute(null=True)
    timeToExist = TTLAttribute(default_for_new=timedelta(hours=24))


class JobStatus(Enum):
    COMPLETED = 1
    RUNNING = 2
    NEW = 3


def get_job_status(query_id):
    # TODO implement caching
    # try:
    #     item = VariantQuery.get(query_id)
    #     if item.complete:
    #         return JobStatus.COMPLETED
    #     else:
    #         return JobStatus.RUNNING
    # except VariantQuery.DoesNotExist:
    return JobStatus.NEW


if __name__ == "__main__":
    pass
