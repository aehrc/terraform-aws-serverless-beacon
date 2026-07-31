import json
import os
import random
import re
import string
from threading import Thread

import boto3
from shared.apiutils import build_bad_request, bundle_response
from shared.athena import Snp, Sample, Genotype, Phenotype
from shared.dynamodb import Dataset as DynamoDataset
from shared.dynamodb.datasets import (
    DATA_TYPE_ILLUMINA,
    DEFAULT_OVINE_ASSEMBLY_ID,
    IlluminaLocations,
)
from smart_open import open as sopen
from file_validator import validate_file, validate_cross_file
from parser import extract

DATASETS_TABLE_NAME = os.environ["DYNAMO_DATASETS_TABLE"]
INDEXER_LAMBDA = os.environ["INDEXER_LAMBDA"]

# uncomment below for debugging
# os.environ['LD_DEBUG'] = 'all'
s3 = boto3.client("s3")
sns = boto3.client("sns")
aws_lambda = boto3.client("lambda")

# progress vars
completed = []
pending = []


def submit_dataset(datasets):
    global pending, completed
    threads = []
    # CHANGED: threads used to be joined without ever checking whether they
    # raised, so a failed ORC upload still returned HTTP 200 and the user was
    # told to note down a dataset id with no data behind it.
    failures = []

    def _upload(model, parsed_dict, label):
        try:
            model.upload_array(parsed_dict)
        except Exception as e:  # noqa: BLE001 - reported to the caller below
            print(f"Upload failed for {label}: {e}")
            failures.append(f"{label}: {e}")

    for dataset in datasets:
        parsed_dict = dataset["result"]
        route_type = dataset["type"]

        if route_type == "snp":
            threads.append(Thread(target=_upload, args=(Snp, parsed_dict, "SNP")))
            threads[-1].start()
            completed.append("Added SNP ORC file")
        elif route_type == "genotype":
            threads.append(
                Thread(target=_upload, args=(Genotype, parsed_dict, "genotype"))
            )
            threads[-1].start()
            completed.append("Added genotype ORC file")
        elif route_type == "sample":
            threads.append(Thread(target=_upload, args=(Sample, parsed_dict, "samples")))
            threads[-1].start()
            completed.append("Added samples ORC file")
        elif route_type == "phenotype":
            threads.append(
                Thread(target=_upload, args=(Phenotype, parsed_dict, "phenotype"))
            )
            threads[-1].start()
            completed.append("Added phenotype ORC file")

    print("Awaiting uploads")
    [thread.join() for thread in threads]
    print("Upload finished")

    return failures

    # if index:
    #     aws_lambda.invoke(
    #         FunctionName=INDEXER_LAMBDA,
    #         InvocationType="Event",
    #         Payload=jsons.dumps(dict()),
    #     )
    #     pending.append("Running indexer")


def register_dataset(dataset_id, s3_bucket, keys, counts, sample_names, assembly_id):
    """
    NEW: write the dataset row to DynamoDB.

    The original imported Dataset and never used it - the id was generated,
    returned to the user, then forgotten, so nothing downstream (the /datasets
    endpoint, the query layer, the frontend) could resolve it.

    Attribute names are taken from shared/dynamodb/datasets.py. Note that
    assemblyId is mandatory in that model (save() raises AttributeNullError
    without it) and is the hash key of the assembly_index GSI, so it has to
    match whatever the query layer sends.
    """
    item = DynamoDataset(dataset_id)
    item.assemblyId = assembly_id
    item.dataType = DATA_TYPE_ILLUMINA
    item.hasPhenotypes = bool(keys.get("phenotype"))
    item.illuminaLocations = IlluminaLocations(
        snp=f"s3://{s3_bucket}/{keys['snp']}",
        sample=f"s3://{s3_bucket}/{keys['sample']}",
        genotypes=[f"s3://{s3_bucket}/{key}" for key in keys["genotype"]],
        phenotypes=[f"s3://{s3_bucket}/{key}" for key in keys.get("phenotype", [])],
    )
    # Reuse the existing counters rather than adding parallel ones, so the
    # Beacon /datasets response is meaningful for both data types.
    item.sampleNames = set(sample_names)
    item.sampleCount = len(sample_names)
    item.variantCount = counts.get("snp", 0)
    item.callCount = counts.get("genotype", 0)
    # createDateTime / updateDateTime are UTCDateTimeAttribute and default
    # themselves - do not assign ISO strings here, PynamoDB will reject them.
    item.save()
    print(f"Registered dataset {dataset_id} ({assembly_id}) in {DATASETS_TABLE_NAME}")


def check_file_exists(s3_bucket, s3_key):
    try:
        s3.head_object(Bucket=s3_bucket, Key=s3_key)
        print("File found successfully")
        return True
    except s3.exceptions.ClientError as e:
        code = e.response["Error"]["Code"]
        if code in {"404", "NoSuchKey"}:
            return False
        # CHANGED: any other code (403 in particular) used to fall through and
        # return None, which the caller reported as "file does not exist" and
        # sent people hunting the wrong problem.
        raise


def parse_file(s3_bucket, s3_key, dataset_id, route_type):
    print(f"Received bucket {s3_bucket}, key {s3_key}")

    if not check_file_exists(s3_bucket, s3_key):
        return bundle_response(
            400, {"message": f"File does not exist on S3. Check your bucket and/or key. Key: {s3_key}"}
        )

    if s3_key.endswith(".txt"):
        delimiter, comment = "\t", "#"
    elif s3_key.endswith(".csv"):
        delimiter, comment = ",", ""
    else:
        return bundle_response(
            400, {"message": f"Unsupported file type. Only .txt or .csv files are supported. Ensure your file has the correct suffix and format. File: {s3_key}"}
        )

    # CHANGED: opened in text mode and streamed line by line. The old version
    # held the raw bytes, the decoded string and the split list at once - the
    # 21 MB example genotype file peaked at ~198 MB of Lambda memory.
    with sopen(f"s3://{s3_bucket}/{s3_key}", "r", encoding="utf-8") as f:
        print(f"Opening file: {s3_key}")
        extracted = extract(
            f, dataset_id, delimiter=delimiter, comment=comment, route_type=route_type
        )

    if not extracted:
        return bundle_response(
            400, {"message": f"Error while parsing file. Check that columns are consistent. File: {s3_key}"}
        )

    validation_error = validate_file(route_type, extracted)

    if validation_error:
        return bundle_response(
            400, {"message": f"Error while validating {s3_key}. {validation_error}"}
        )

    return extracted


def route(event, route_type=""):
    # reset progress vars
    global completed, pending

    completed = []
    pending = []
    extracted_outputs = []

    event_body = event.get("body")

    if not event_body:
        return bundle_response(400, {"message": "No body sent with request."})

    try:
        body_dict = json.loads(event_body)
    except ValueError:
        return bundle_response(
            400, {"message": "Error parsing request body, Expected JSON."}
        )

    s3_bucket = body_dict.get("s3_bucket")

    if not s3_bucket:
        return bundle_response(400, {"message": "No bucket specified."})

    dataset_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12)
)

    # SNP, sample and genotype files are required to establish the database
    snp_key = body_dict.get("snp_key")
    sample_key = body_dict.get("sample_key")
    genotype_keys = body_dict.get("genotype_keys")
    phenotype_keys = body_dict.get("phenotype_keys") or []
    # CHANGED: assemblyId is mandatory on the Dataset model. Allow the caller to
    # state it; default to the ovine build rather than a human assembly.
    assembly_id = body_dict.get("assembly_id") or DEFAULT_OVINE_ASSEMBLY_ID

    if not snp_key or not sample_key or not genotype_keys:
        return bundle_response(400, {"message": "You must supply keys for SNP, Sample and Genotype file/s when creating a dataset."})

    extracted_outputs.append({"result": parse_file(s3_bucket, snp_key, dataset_id, "snp"), "type": "snp"})
    extracted_outputs.append({"result": parse_file(s3_bucket, sample_key, dataset_id, "sample"), "type": "sample"})
    for genotype_key in genotype_keys:
        extracted_outputs.append({"result": parse_file(s3_bucket, genotype_key, dataset_id, "genotype"), "type": "genotype"})

    # Phenotype files are optional
    for phenotype_key in phenotype_keys:
        extracted_outputs.append({"result": parse_file(s3_bucket, phenotype_key, dataset_id, "phenotype"), "type": "phenotype"})

    errors = []

    # All uploaded files must be valid to establish the dataset
    for output in extracted_outputs:
        if (isinstance(output["result"], dict)):
            errors.append(output["result"])

    # CHANGED: the files must also agree with each other before anything is
    # uploaded - see validate_cross_file.
    if not errors:
        by_type = {"snp": [], "sample": [], "genotype": [], "phenotype": []}
        for output in extracted_outputs:
            by_type[output["type"]].extend(output["result"])

        cross_error = validate_cross_file(
            by_type["snp"], by_type["sample"], by_type["genotype"], by_type["phenotype"]
        )
        if cross_error:
            errors.append({"message": cross_error})

    if errors:
        print(f"Errors found: {errors}")
        return bundle_response(400, {"message": "Dataset validation failed. No files were uploaded.", "errors": errors})

    failures = submit_dataset(extracted_outputs)

    if failures:
        return bundle_response(
            500,
            {
                "message": "One or more files failed to upload. The dataset was not registered.",
                "errors": failures,
                "completed": completed,
            },
        )

    # CHANGED: register the dataset so the id actually resolves.
    try:
        register_dataset(
            dataset_id,
            s3_bucket,
            {
                "snp": snp_key,
                "sample": sample_key,
                "genotype": genotype_keys,
                "phenotype": phenotype_keys,
            },
            counts={k: len(v) for k, v in by_type.items()},
            sample_names={row["sample_id"] for row in by_type["sample"]},
            assembly_id=assembly_id,
        )
        completed.append("Registered dataset")
    except Exception as e:  # noqa: BLE001
        print(f"Dataset registration failed: {e}")
        return bundle_response(
            500,
            {
                "message": "Files were uploaded but the dataset could not be registered.",
                "errors": [str(e)],
                "completed": completed,
            },
        )

    return bundle_response(200, {"message": "Successfully scheduled data for submission. Please note down your dataset ID.", "datasetId": dataset_id, "errors": errors, "pending": pending, "completed": completed})


if __name__ == "__main__":
    pass
