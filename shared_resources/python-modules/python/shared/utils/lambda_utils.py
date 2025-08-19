import contextlib
import tempfile
import shutil
import os
import time
import random

import botocore
import boto3


THROTTLE_DELAYS = [0.1 * i for i in range(1, 6)]


# from https://bitbucket.csiro.au/users/jai014/repos/covidbeacon/browse
class Timer:
    def __init__(self):
        self.start_time = time.time()

    def passed(self):
        return int((time.time() - self.start_time) * 1000)

    @property
    def str(self):
        return f"{self.passed()}ms"


# from https://bitbucket.csiro.au/users/jai014/repos/covidbeacon/browse
class LambdaClient:
    def __init__(self):
        lambda_config = botocore.config.Config(
            read_timeout=300,
            max_pool_connections=500,
            retries={
                "total_max_attempts": 1,
            },
        )
        self.client = boto3.client("lambda", config=lambda_config)

    def invoke(self, **kwargs):
        while True:
            try:
                response = self.client.invoke(**kwargs)
            except botocore.exceptions.ClientError as error:
                response = error.response
                if response["Error"]["Code"] == "TooManyRequestsException":
                    time.sleep(random.choice(THROTTLE_DELAYS))
                    continue
                elif response["Error"]["Code"] == "ServiceException":
                    time.sleep(random.choice(THROTTLE_DELAYS))
                    continue
                else:
                    raise error
            else:
                return response


class BeaconEnvironment:
    @property
    def BEACON_API_VERSION(self):
        return os.environ["BEACON_API_VERSION"]

    @property
    def BEACON_ID(self):
        return os.environ["BEACON_ID"]

    @property
    def BEACON_NAME(self):
        return os.environ["BEACON_NAME"]

    @property
    def BEACON_ENVIRONMENT(self):
        return os.environ["BEACON_ENVIRONMENT"]

    @property
    def BEACON_DESCRIPTION(self):
        return os.environ["BEACON_DESCRIPTION"]

    @property
    def BEACON_VERSION(self):
        return os.environ["BEACON_VERSION"]

    @property
    def BEACON_WELCOME_URL(self):
        return os.environ["BEACON_WELCOME_URL"]

    @property
    def BEACON_ALTERNATIVE_URL(self):
        return os.environ["BEACON_ALTERNATIVE_URL"]

    @property
    def BEACON_CREATE_DATETIME(self):
        return os.environ["BEACON_CREATE_DATETIME"]

    @property
    def BEACON_UPDATE_DATETIME(self):
        return os.environ["BEACON_UPDATE_DATETIME"]

    @property
    def BEACON_HANDOVERS(self):
        return os.environ["BEACON_HANDOVERS"]

    @property
    def BEACON_DOCUMENTATION_URL(self):
        return os.environ["BEACON_DOCUMENTATION_URL"]

    @property
    def BEACON_DEFAULT_GRANULARITY(self):
        return os.environ["BEACON_DEFAULT_GRANULARITY"]

    @property
    def BEACON_URI(self):
        return os.environ["BEACON_URI"]

    @property
    def BEACON_ORG_ID(self):
        return os.environ["BEACON_ORG_ID"]

    @property
    def BEACON_ORG_NAME(self):
        return os.environ["BEACON_ORG_NAME"]

    @property
    def BEACON_ORG_DESCRIPTION(self):
        return os.environ["BEACON_ORG_DESCRIPTION"]

    @property
    def BEACON_ORG_ADDRESS(self):
        return os.environ["BEACON_ORG_ADDRESS"]

    @property
    def BEACON_ORG_WELCOME_URL(self):
        return os.environ["BEACON_ORG_WELCOME_URL"]

    @property
    def BEACON_ORG_CONTACT_URL(self):
        return os.environ["BEACON_ORG_CONTACT_URL"]

    @property
    def BEACON_ORG_LOGO_URL(self):
        return os.environ["BEACON_ORG_LOGO_URL"]

    @property
    def BEACON_SERVICE_TYPE_GROUP(self):
        return os.environ["BEACON_SERVICE_TYPE_GROUP"]

    @property
    def BEACON_SERVICE_TYPE_ARTIFACT(self):
        return os.environ["BEACON_SERVICE_TYPE_ARTIFACT"]

    @property
    def BEACON_SERVICE_TYPE_VERSION(self):
        return os.environ["BEACON_SERVICE_TYPE_VERSION"]

    @property
    def BEACON_ENABLE_AUTH(self):
        return os.environ["BEACON_ENABLE_AUTH"].strip().lower() in ("true", "1")


class AthenaEnvironment:
    @property
    def ATHENA_WORKGROUP(self):
        return os.environ["ATHENA_WORKGROUP"]

    @property
    def ATHENA_METADATA_DATABASE(self):
        return os.environ["ATHENA_METADATA_DATABASE"]

    @property
    def ATHENA_METADATA_BUCKET(self):
        return os.environ["ATHENA_METADATA_BUCKET"]

    @property
    def ATHENA_DATASETS_TABLE(self):
        return os.environ["ATHENA_DATASETS_TABLE"]

    @property
    def ATHENA_DATASETS_CACHE_TABLE(self):
        return os.environ["ATHENA_DATASETS_CACHE_TABLE"]

    @property
    def ATHENA_COHORTS_TABLE(self):
        return os.environ["ATHENA_COHORTS_TABLE"]

    @property
    def ATHENA_COHORTS_CACHE_TABLE(self):
        return os.environ["ATHENA_COHORTS_CACHE_TABLE"]

    @property
    def ATHENA_INDIVIDUALS_TABLE(self):
        return os.environ["ATHENA_INDIVIDUALS_TABLE"]

    @property
    def ATHENA_INDIVIDUALS_CACHE_TABLE(self):
        return os.environ["ATHENA_INDIVIDUALS_CACHE_TABLE"]

    @property
    def ATHENA_BIOSAMPLES_TABLE(self):
        return os.environ["ATHENA_BIOSAMPLES_TABLE"]

    @property
    def ATHENA_BIOSAMPLES_CACHE_TABLE(self):
        return os.environ["ATHENA_BIOSAMPLES_CACHE_TABLE"]

    @property
    def ATHENA_RUNS_TABLE(self):
        return os.environ["ATHENA_RUNS_TABLE"]

    @property
    def ATHENA_RUNS_CACHE_TABLE(self):
        return os.environ["ATHENA_RUNS_CACHE_TABLE"]

    @property
    def ATHENA_ANALYSES_TABLE(self):
        return os.environ["ATHENA_ANALYSES_TABLE"]

    @property
    def ATHENA_ANALYSES_CACHE_TABLE(self):
        return os.environ["ATHENA_ANALYSES_CACHE_TABLE"]

    @property
    def ATHENA_TERMS_TABLE(self):
        return os.environ["ATHENA_TERMS_TABLE"]

    @property
    def ATHENA_TERMS_INDEX_TABLE(self):
        return os.environ["ATHENA_TERMS_INDEX_TABLE"]

    @property
    def ATHENA_TERMS_CACHE_TABLE(self):
        return os.environ["ATHENA_TERMS_CACHE_TABLE"]

    @property
    def ATHENA_RELATIONS_TABLE(self):
        return os.environ["ATHENA_RELATIONS_TABLE"]


class DynamoDBEnvironment:
    @property
    def DYNAMO_DATASETS_TABLE(self):
        return os.environ["DYNAMO_DATASETS_TABLE"]

    @property
    def DYNAMO_VCF_SUMMARIES_TABLE(self):
        return os.environ["DYNAMO_VCF_SUMMARIES_TABLE"]

    @property
    def DYNAMO_VARIANT_DUPLICATES_TABLE(self):
        return os.environ["DYNAMO_VARIANT_DUPLICATES_TABLE"]

    @property
    def DYNAMO_VARIANT_QUERIES_TABLE(self):
        return os.environ["DYNAMO_VARIANT_QUERIES_TABLE"]

    @property
    def DYNAMO_VARIANT_QUERY_RESPONSES_TABLE(self):
        return os.environ["DYNAMO_VARIANT_QUERY_RESPONSES_TABLE"]

    @property
    def DYNAMO_ONTOLOGIES_TABLE(self):
        return os.environ["DYNAMO_ONTOLOGIES_TABLE"]

    @property
    def DYNAMO_TERM_LABELS_TABLE(self):
        return os.environ["DYNAMO_TERM_LABELS_TABLE"]

    @property
    def DYNAMO_ANSCESTORS_TABLE(self):
        return os.environ["DYNAMO_ANSCESTORS_TABLE"]

    @property
    def DYNAMO_DESCENDANTS_TABLE(self):
        return os.environ["DYNAMO_DESCENDANTS_TABLE"]

    @property
    def DYNAMO_ONTO_INDEX_TABLE(self):
        return os.environ["DYNAMO_ONTO_INDEX_TABLE"]


class SnsEnvironment:
    @property
    def INDEXER_TOPIC_ARN(self):
        return os.environ["INDEXER_TOPIC_ARN"]


class CognitoEnvironment:
    @property
    def COGNITO_USER_POOL_ID(self):
        return os.environ["COGNITO_USER_POOL_ID"]


class ConfigEnvironment:
    @property
    def CONFIG_MAX_VARIANT_SEARCH_BASE_RANGE(self):
        return int(os.environ["CONFIG_MAX_VARIANT_SEARCH_BASE_RANGE"])


def clear_tmp():
    try:
        for file_name in os.listdir("/tmp"):
            file_path = "/tmp/" + file_name
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
    except Exception as e:
        print("Unable to clean temp\n", e)


@contextlib.contextmanager
def make_temp_file():
    # the race condition does not affect
    # lambdas as only one request processed at
    # any given time
    tempf = tempfile.mktemp()
    try:
        yield tempf
    finally:
        os.unlink(tempf)


ENV_BEACON = BeaconEnvironment()
ENV_ATHENA = AthenaEnvironment()
ENV_DYNAMO = DynamoDBEnvironment()
ENV_SNS = SnsEnvironment()
ENV_CONFIG = ConfigEnvironment()
ENV_COGNITO = CognitoEnvironment()
