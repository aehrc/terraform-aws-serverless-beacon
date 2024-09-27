import json
import os
from threading import Thread

import boto3
import jsons
from jsonschema import Draft202012Validator, RefResolver
from shared.apiutils import build_bad_request, bundle_response
from shared.athena import Analysis, Biosample, Cohort, Dataset, Individual, Run
from shared.dynamodb import Dataset as DynamoDataset
from shared.utils import clear_tmp
from smart_open import open as sopen
from util import get_vcf_chromosome_maps

DATASETS_TABLE_NAME = os.environ["DYNAMO_DATASETS_TABLE"]
INDEXER_LAMBDA = os.environ["INDEXER_LAMBDA"]

# uncomment below for debugging
# os.environ['LD_DEBUG'] = 'all'
sns = boto3.client("sns")
aws_lambda = boto3.client("lambda")

# progress vars
completed = []
pending = []


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
            item.save()
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
            threads.append(Thread(target=Dataset.upload_array, args=([dataset],)))
            threads[-1].start()
            completed.append("Added dataset metadata")

    if datasetId and cohortId:
        print("De-serialising started")
        individuals = attributes.get("individuals", [])
        biosamples = attributes.get("biosamples", [])
        runs = attributes.get("runs", [])
        analyses = attributes.get("analyses", [])
        print("De-serialising complete")

        # setting dataset id
        # private attributes inside entities are parsed properly
        # for example _vcfSampleId is mapped to vcfSampleId
        for individual in individuals:
            individual["_datasetId"] = datasetId
            individual["_cohortId"] = cohortId

        for biosample in biosamples:
            biosample["_datasetId"] = datasetId
            biosample["_cohortId"] = cohortId

        for run in runs:
            run["_datasetId"] = datasetId
            run["_cohortId"] = cohortId

        for analysis in analyses:
            analysis["_datasetId"] = datasetId
            analysis["_cohortId"] = cohortId

        # upload to s3
        if len(individuals) > 0:
            threads.append(Thread(target=Individual.upload_array, args=(individuals,)))
            threads[-1].start()
            completed.append("Added individuals")

        if len(biosamples) > 0:
            threads.append(Thread(target=Biosample.upload_array, args=(biosamples,)))
            threads[-1].start()
            completed.append("Added biosamples")

        if len(runs) > 0:
            threads.append(Thread(target=Run.upload_array, args=(runs,)))
            threads[-1].start()
            completed.append("Added runs")

        if len(analyses) > 0:
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


def update_dataset(body_dict):
    global pending, completed
    summarise = False

    if len(vcf_locations := set(body_dict.get("vcfLocations", []))) > 0:
        summarise = True

    errored, errors, vcf_chromosome_maps = get_vcf_chromosome_maps(vcf_locations)
    if errored:
        return bundle_response(
            400, build_bad_request(code=400, message="\n".join(errors))
        )
    print("Validated the VCF files")

    create_dataset(body_dict, vcf_chromosome_maps)

    return bundle_response(200, {"Completed": completed, "Running": pending})


def validate_request(parameters):
    # load validator
    update_schema = "./schemas/submit-dataset-schema-update.json"
    schema_dir = os.path.dirname(os.path.abspath(update_schema))
    update_schema = json.load(open(update_schema))
    resolver = RefResolver(
        base_uri="file://" + schema_dir + "/", referrer=update_schema
    )
    validator = Draft202012Validator(update_schema, resolver=resolver)
    errors = []

    for error in sorted(validator.iter_errors(parameters), key=lambda e: e.path):
        error_message = f"{error.message} "
        for part in list(error.path):
            error_message += f"/{part}"
        errors.append(error_message)
    return errors


def route(event, id):
    # reset progress vars
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

    if validation_errors := validate_request(body_dict):
        print(", ".join(validation_errors))
        return bundle_response(
            400, build_bad_request(code=400, message=", ".join(validation_errors))
        )
    print("Validated the payload")

    # TODO implement an efficient update scheme
    # result = update_dataset(body_dict)
    clear_tmp()
    return None


if __name__ == "__main__":
    pass
