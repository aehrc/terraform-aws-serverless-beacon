from threading import Thread
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
import subprocess
import json
import os

from jsonschema import Draft202012Validator, RefResolver
from smart_open import open as sopen
import jsons
import boto3

from shared.utils import get_vcf_chromosomes, clear_tmp
from shared.apiutils import build_bad_request, bundle_response
from shared.dynamodb import Dataset as DynamoDataset, VcfChromosomeMap
from shared.athena import Dataset, Cohort, Individual, Biosample, Run, Analysis


DATASETS_TABLE_NAME = os.environ["DYNAMO_DATASETS_TABLE"]
SUMMARISE_DATASET_SNS_TOPIC_ARN = os.environ["SUMMARISE_DATASET_SNS_TOPIC_ARN"]
INDEXER_LAMBDA = os.environ["INDEXER_LAMBDA"]

# uncomment below for debugging
# os.environ['LD_DEBUG'] = 'all'

sns = boto3.client("sns")
aws_lambda = boto3.client("lambda")

newSchema = "./schemas/submitDataset-schema-new.json"
updateSchema = "./schemas/submitDataset-schema-update.json"
# get schema dir
schema_dir = os.path.dirname(os.path.abspath(newSchema))
# loading schemas
newSchema = json.load(open(newSchema))
updateSchema = json.load(open(updateSchema))
resolveNew = RefResolver(base_uri="file://" + schema_dir + "/", referrer=newSchema)
resolveUpdate = RefResolver(
    base_uri="file://" + schema_dir + "/", referrer=updateSchema
)
completed = []
pending = []


def get_vcf_chromosome_maps(vcf_location):
    errored, error, chroms = get_vcf_chromosomes(vcf_location)
    vcf_chromosome_map = None
    if not errored:
        vcf_chromosome_map = VcfChromosomeMap()
        vcf_chromosome_map.vcf = vcf_location
        vcf_chromosome_map.chromosomes = chroms

    return errored, error, vcf_chromosome_map


def create_dataset(attributes, vcf_chromosome_maps):
    datasetId = attributes.get("datasetId", None)
    cohortId = attributes.get("cohortId", None)
    index = attributes.get("index", False)
    global pending, completed
    threads = []

    if datasetId:
        json_dataset = attributes.get("dataset", None)
        if json_dataset:
            # dataset information
            item = DynamoDataset(datasetId)
            item.assemblyId = attributes.get("assemblyId", "UNKNOWN")
            item.vcfLocations = attributes.get("vcfLocations", [])
            item.vcfGroups = attributes.get("vcfGroups", [item.vcfLocations])
            item.vcfChromosomeMap = vcf_chromosome_maps

            print(f"Putting item in table: {item.to_json()}")
            item.save()
            print(f"Putting complete")
            completed.append("Added dataset info")

            # dataset metadata entry information
            dataset = jsons.load(json_dataset, Dataset)
            dataset.id = datasetId
            dataset._assemblyId = item.assemblyId
            dataset._vcfLocations = item.vcfLocations
            dataset._vcfChromosomeMap = [
                vcfm.attribute_values for vcfm in vcf_chromosome_maps
            ]
            dataset.createDateTime = str(item.createDateTime)
            dataset.updateDateTime = str(item.updateDateTime)
            # Dataset.upload_array([dataset])
            threads.append(Thread(target=Dataset.upload_array, args=([dataset],)))
            threads[-1].start()
            completed.append("Added dataset metadata")

    if datasetId and cohortId:
        print("De-serialising started")
        individuals = jsons.default_list_deserializer(
            attributes.get("individuals", []), List[Individual]
        )
        biosamples = jsons.default_list_deserializer(
            attributes.get("biosamples", []), List[Biosample]
        )
        runs = jsons.default_list_deserializer(attributes.get("runs", []), List[Run])
        analyses = jsons.default_list_deserializer(
            attributes.get("analyses", []), List[Analysis]
        )
        print("De-serialising complete")

        # setting dataset id
        # private attributes inside entities are parsed properly
        # for example _vcfSampleId is mapped to vcfSampleId
        for individual in individuals:
            individual._datasetId = datasetId
            individual._cohortId = cohortId

        for biosample in biosamples:
            biosample._datasetId = datasetId
            biosample._cohortId = cohortId
        for run in runs:
            run._datasetId = datasetId
            run._cohortId = cohortId
        for analysis in analyses:
            analysis._datasetId = datasetId
            analysis._cohortId = cohortId

        # upload to s3
        if len(individuals) > 0:
            # Individual.upload_array(individuals)
            threads.append(Thread(target=Individual.upload_array, args=(individuals,)))
            threads[-1].start()
            completed.append("Added individuals")
        if len(biosamples) > 0:
            # Biosample.upload_array(biosamples)
            threads.append(Thread(target=Biosample.upload_array, args=(biosamples,)))
            threads[-1].start()
            completed.append("Added biosamples")
        if len(runs) > 0:
            # Run.upload_array(runs)
            threads.append(Thread(target=Run.upload_array, args=(runs,)))
            threads[-1].start()
            completed.append("Added runs")
        if len(analyses) > 0:
            # Analysis.upload_array(analyses)
            threads.append(Thread(target=Analysis.upload_array, args=(analyses,)))
            threads[-1].start()
            completed.append("Added analyses")

    if cohortId:
        # cohort information
        json_cohort = attributes.get("cohort", None)
        if json_cohort:
            cohort = jsons.load(json_cohort, Cohort)
            cohort.id = cohortId
            # Cohort.upload_array([cohort])
            threads.append(Thread(target=Cohort.upload_array, args=([cohort],)))
            threads[-1].start()
            completed.append("Added cohorts")

    print("Awaiting uploads")
    [thread.join() for thread in threads]
    print("Upload finished")

    if index:
        aws_lambda.invoke(
            FunctionName=INDEXER_LAMBDA,
            InvocationType="Event",
            Payload=jsons.dumps(dict()),
        )
        pending.append("Running indexer")


def submit_dataset(body_dict, method):
    new = method == "POST"
    validation_errors = validate_request(body_dict, new)
    global pending, completed

    if validation_errors:
        print()
        print(", ".join(validation_errors))
        return bundle_response(
            400, build_bad_request(code=400, message=", ".join(validation_errors))
        )
    print("Validated the payload")
    if "vcfLocations" in body_dict:
        # resolve VCF chromosomes in parallel
        executor = ThreadPoolExecutor(32)
        errored = False
        errors = []
        vcf_chromosome_maps = []
        vcf_chromosome_map_futures = [
            executor.submit(get_vcf_chromosome_maps, vcf_location)
            for vcf_location in set(body_dict["vcfLocations"])
        ]

        for vcf_chromosome_map_future in as_completed(vcf_chromosome_map_futures):
            (
                task_errored,
                error,
                vcf_chromosome_map,
            ) = vcf_chromosome_map_future.result()
            errored = errored or task_errored
            errors.append(error)
            vcf_chromosome_maps.append(vcf_chromosome_map)

        executor.shutdown()
        if errored:
            return bundle_response(
                400, build_bad_request(code=400, message="\n".join(errors))
            )
        summarise = True
    else:
        summarise = False
    print("Validated the VCF files")
    # handle data set submission or update
    if new:
        create_dataset(body_dict, vcf_chromosome_maps)
    else:
        update_dataset(body_dict, vcf_chromosome_maps)

    # if summarise:
    #     summarise_dataset(body_dict['datasetId'])
    #     pending.append('Summarising')
    clear_tmp()
    return bundle_response(200, {"Completed": completed, "Running": pending})


def summarise_dataset(dataset):
    kwargs = {"TopicArn": SUMMARISE_DATASET_SNS_TOPIC_ARN, "Message": dataset}
    print("Publishing to SNS: {}".format(json.dumps(kwargs)))
    response = sns.publish(**kwargs)
    print("Received Response: {}".format(json.dumps(response)))


def update_dataset(attributes):
    # TODO see how other entities can be updated or overwritten
    datasetId = attributes["datasetId"]
    item = DynamoDataset.get(datasetId)
    actions = []
    actions += (
        [DynamoDataset.assemblyId.set(attributes["assemblyId"])]
        if attributes.get("assemblyId", False)
        else []
    )
    actions += (
        [DynamoDataset.vcfLocations.set(attributes["vcfLocations"])]
        if attributes.get("vcfLocations", False)
        else []
    )
    actions += (
        [DynamoDataset.vcfGroups.set(attributes["vcfGroups"])]
        if attributes.get("vcfGroups", False)
        else []
    )

    print(f"Updating table: {item.to_json()}")
    item.update(actions=actions)


def validate_request(parameters, new):
    validator = None
    # validate request body with schema for a new submission or update
    if new:
        validator = Draft202012Validator(newSchema, resolver=resolveNew)
    else:
        validator = Draft202012Validator(updateSchema, resolver=resolveUpdate)

    errors = []

    for error in sorted(validator.iter_errors(parameters), key=lambda e: e.path):
        error_message = f"{error.message} "
        for part in list(error.path):
            error_message += f"/{part}"
        errors.append(error_message)
    return errors


def lambda_handler(event, context):
    # print('Event Received: {}'.format(json.dumps(event)))
    global completed, pending

    completed = []
    pending = []

    event_body = event.get("body")

    if not event_body:
        return bundle_response(
            400, build_bad_request(code=400, message="No body sent with request.")
        )
    try:
        body_dict = json.loads(event_body)

        if body_dict.get("s3Payload"):
            print("Using s3 payload instead of POST body")

            with sopen(body_dict.get("s3Payload"), "r") as payload:
                body_dict = json.loads(payload.read())
    except ValueError:
        return bundle_response(
            400,
            build_bad_request(
                code=400, message="Error parsing request body, Expected JSON."
            ),
        )

    method = event["httpMethod"]
    return submit_dataset(body_dict, method)


if __name__ == "__main__":
    pass
