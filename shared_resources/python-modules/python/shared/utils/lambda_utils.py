import contextlib
import os
import shutil
import tempfile


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
    def ATHENA_COHORTS_TABLE(self):
        return os.environ["ATHENA_COHORTS_TABLE"]

    @property
    def ATHENA_INDIVIDUALS_TABLE(self):
        return os.environ["ATHENA_INDIVIDUALS_TABLE"]

    @property
    def ATHENA_BIOSAMPLES_TABLE(self):
        return os.environ["ATHENA_BIOSAMPLES_TABLE"]

    @property
    def ATHENA_RUNS_TABLE(self):
        return os.environ["ATHENA_RUNS_TABLE"]

    @property
    def ATHENA_ANALYSES_TABLE(self):
        return os.environ["ATHENA_ANALYSES_TABLE"]

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
    def DYNAMO_ANSCESTORS_TABLE(self):
        return os.environ["DYNAMO_ANSCESTORS_TABLE"]

    @property
    def DYNAMO_DESCENDANTS_TABLE(self):
        return os.environ["DYNAMO_DESCENDANTS_TABLE"]

    @property
    def DYNAMO_ONTO_INDEX_TABLE(self):
        return os.environ["DYNAMO_ONTO_INDEX_TABLE"]


def clear_tmp():
    for file_name in os.listdir("/tmp"):
        file_path = "/tmp/" + file_name
        if os.path.isfile(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)


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
