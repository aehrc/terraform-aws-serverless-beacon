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
            json_dataset["id"] = datasetId
            json_dataset["assemblyId"] = item.assemblyId
            json_dataset["vcfLocations"] = item.vcfLocations
            json_dataset["vcfChromosomeMap"] = [
                vcfm.attribute_values for vcfm in vcf_chromosome_maps
            ]
            json_dataset["createDateTime"] = str(item.createDateTime)
            json_dataset["updateDateTime"] = str(item.updateDateTime)
            threads.append(Thread(target=Dataset.upload_array, args=([json_dataset],)))
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
        # for example _vcfSampleId is mapped to vcfSampleId
        # skip _ in private variables
        # they are handled in the upload function
        for individual in individuals:
            individual["datasetId"] = datasetId
            individual["cohortId"] = cohortId

        for biosample in biosamples:
            biosample["datasetId"] = datasetId
            biosample["cohortId"] = cohortId

        for run in runs:
            run["datasetId"] = datasetId
            run["cohortId"] = cohortId

        for analysis in analyses:
            analysis["datasetId"] = datasetId
            analysis["cohortId"] = cohortId

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
            json_cohort["cohortSize"] = len(attributes.get("individuals", []))
            json_cohort["id"] = cohortId
            # Cohort.upload_array([cohort])
            threads.append(Thread(target=Cohort.upload_array, args=([json_cohort],)))
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


def submit_dataset(body_dict):
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
    new_schema = "./schemas/submit-dataset-schema-new.json"
    schema_dir = os.path.dirname(os.path.abspath(new_schema))
    new_schema = json.load(open(new_schema))
    resolveNew = RefResolver(base_uri="file://" + schema_dir + "/", referrer=new_schema)
    validator = Draft202012Validator(new_schema, resolver=resolveNew)
    errors = []

    for error in sorted(validator.iter_errors(parameters), key=lambda e: e.path):
        error_message = f"{error.message} "
        for part in list(error.path):
            error_message += f"/{part}"
        errors.append(error_message)
    return errors


def route(event):
    # reset progress vars
    global completed, pending

    completed = []
    pending = []

    event_body = event.get("body")

    if not event_body:
        return bundle_response(400, {"message": "No body sent with request."})
    try:
        body_dict = json.loads(event_body)

        if body_dict.get("s3Payload"):
            print("Using s3 payload instead of POST body")

            with sopen(body_dict.get("s3Payload"), "r") as payload:
                body_dict = json.loads(payload.read())
    except ValueError:
        return bundle_response(
            400, {"message": "Error parsing request body, Expected JSON."}
        )

    if validation_errors := validate_request(body_dict):
        print(", ".join(validation_errors))
        return bundle_response(400, {"message": validation_errors})
    print("Validated the payload")

    result = submit_dataset(body_dict)
    clear_tmp()
    return result


if __name__ == "__main__":
    pass
