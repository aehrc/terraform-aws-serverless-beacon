import datetime
import json
import os
import subprocess
from typing import List
from jsonschema import Draft7Validator, RefResolver
import jsons
import tempfile

import boto3

from apiutils.api_response import bad_request, bundle_response
from utils.chrom_matching import get_vcf_chromosomes
from dynamodb.datasets import Dataset as DynamoDataset, VcfChromosomeMap
from athena.dataset import Dataset
from athena.cohort import Cohort
from athena.individual import Individual
from athena.biosample import Biosample
from athena.run import Run
from athena.analysis import Analysis


DATASETS_TABLE_NAME = os.environ['DYNAMO_DATASETS_TABLE']
SUMMARISE_DATASET_SNS_TOPIC_ARN = os.environ['SUMMARISE_DATASET_SNS_TOPIC_ARN']
INDEXER_LAMBDA = os.environ['INDEXER_LAMBDA']

# uncomment below for debugging
# os.environ['LD_DEBUG'] = 'all'

sns = boto3.client('sns')
aws_lambda = boto3.client('lambda')

newSchema = "./schemas/submitDataset-schema-new.json"
updateSchema = "./schemas/submitDataset-schema-update.json"
# get schema dir
schema_dir = os.path.dirname(os.path.abspath(newSchema))
# loading schemas
newSchema = json.load(open(newSchema))
updateSchema = json.load(open(updateSchema))
resolveNew = RefResolver(base_uri = 'file://' + schema_dir + '/', referrer = newSchema)
resolveUpdate = RefResolver(base_uri = 'file://' + schema_dir + '/', referrer = updateSchema)

# just checking if the tabix would work as expected on a valid vcf.gz file
# validate if the index file exists too
def check_vcf_locations(locations):
    errors = []
    for location in locations:
        try:
            subprocess.check_output(
                args=[
                    'tabix',
                    '--list-chroms',
                    location,
                ],
                stderr=subprocess.PIPE,
                cwd='/tmp',
                encoding='utf-8',
            )
        except subprocess.CalledProcessError as e:
            error_message = e.stderr
            print("cmd {} returned non-zero error code {}. stderr:\n{}".format(
                e.cmd, e.returncode, error_message
            ))
            if error_message.startswith("[E::hts_open_format] Failed to open"):
                errors.append("Could not access {}.".format(location))
            elif error_message.startswith("[E::hts_hopen] Failed to open"):
                errors.append("{} is not a gzipped vcf file.".format(location))
            elif error_message.startswith("Could not load .tbi index"):
                errors.append("Could not open index file for {}.".format(
                    location))
            else:
                raise e
    return "\n".join(errors)


def create_dataset(attributes):
    item = DynamoDataset(attributes['dataset']['id'])
    item.assemblyId = attributes['assemblyId']
    item.vcfLocations = attributes.get('vcfLocations', [])
    item.vcfGroups = attributes.get('vcfGroups', [item.vcfLocations])

    # must have dataset and cohort information
    dataset = jsons.load(attributes.get('dataset'), Dataset)
    cohort = jsons.load(attributes.get('cohort'), Cohort)
    individuals = jsons.default_list_deserializer(attributes.get('individuals', []), List[Individual])
    biosamples = jsons.default_list_deserializer(attributes.get('biosamples', []), List[Biosample])
    runs = jsons.default_list_deserializer(attributes.get('runs', []), List[Run])
    analyses = jsons.default_list_deserializer(attributes.get('analyses', []), List[Analysis])
    
    # setting dataset id
    for individual in individuals:
        individual.datasetId = dataset.id
        individual.cohortId = cohort.id
    for biosample in biosamples:
        biosample.datasetId = dataset.id
        biosample.cohortId = cohort.id
    for run in runs:
        run.datasetId = dataset.id
        run.cohortId = cohort.id
    for analysis in analyses:
        analysis.datasetId = dataset.id
        analysis.cohortId = cohort.id

    # upload the dataset and cohort info
    Dataset.upload_array([dataset])
    Cohort.upload_array([cohort])

    # upload to s3
    if len(individuals) > 0:
        Individual.upload_array(individuals)
    if len(biosamples) > 0: 
        Biosample.upload_array(biosamples)
    if len(runs) > 0:
        Run.upload_array(runs)
    if len(analyses) > 0: 
        Analysis.upload_array(analyses)

    aws_lambda.invoke(
        FunctionName=INDEXER_LAMBDA,
        InvocationType='Event',
        Payload=jsons.dumps(dict()),
    )

    for vcf in set(item.vcfLocations):
        chroms = get_vcf_chromosomes(vcf)
        vcfm = VcfChromosomeMap()
        vcfm.vcf = vcf
        vcfm.chromosomes = chroms
        item.vcfChromosomeMap.append(vcfm)

    print(f"Putting item in table: {item.to_json()}")
    item.save()


def get_current_time():
    d = datetime.datetime.now(datetime.timezone.utc)
    return d.strftime('%Y-%m-%dT%H:%M:%S.%f%z')


def submit_dataset(body_dict, method):
    new = method == 'POST'
    validation_error = validate_request(body_dict, new)
    if validation_error:
        return bad_request(errorMessage=validation_error)

    if 'vcfLocations' in body_dict:
        # validate vcf files if skipCheck is not specified 
        if 'skipCheck' not in body_dict:
            errors = check_vcf_locations(body_dict['vcfLocations'])
            if errors:
                return bad_request(errorMessage=errors)
        summarise = True
    else:
        summarise = False
    # handle data set submission or update
    if new:
        create_dataset(body_dict)
    else:
        update_dataset(body_dict)
    
    if summarise:
        summarise_dataset(body_dict['dataset']['id'])

    return bundle_response(200, {})


def summarise_dataset(dataset):
    kwargs = {
        'TopicArn': SUMMARISE_DATASET_SNS_TOPIC_ARN,
        'Message': dataset
    }
    print('Publishing to SNS: {}'.format(json.dumps(kwargs)))
    response = sns.publish(**kwargs)
    print('Received Response: {}'.format(json.dumps(response)))


def update_dataset(attributes):
    # TODO see how other entities can be updated or overwritten
    item = DynamoDataset.get(attributes['dataset']['id'])
    actions = []
    actions += [DynamoDataset.assemblyId.set(attributes['assemblyId'])] if attributes.get('assemblyId', False) else []
    actions += [DynamoDataset.vcfLocations.set(attributes['vcfLocations'])] if attributes.get('vcfLocations', False) else []
    actions += [DynamoDataset.vcfGroups.set(attributes['vcfGroups'])] if attributes.get('vcfGroups', False) else []

    print(f"Updating table: {item.to_json()}")
    item.update(actions=actions)


def validate_request(parameters, new):
    validator = None
    # validate request body with schema for a new submission or update
    if new:
        validator = Draft7Validator(newSchema, resolver=resolveNew)
    else:
        validator = Draft7Validator(updateSchema, resolver=resolveUpdate)

    errors = sorted(validator.iter_errors(parameters), key=lambda e: e.path)
    return [error.message for error in errors]


def lambda_handler(event, context):
    print('Event Received: {}'.format(json.dumps(event)))
    event_body = event.get('body')

    if not event_body:
        return bad_request(errorMessage='No body sent with request.')
    try:
        body_dict = json.loads(event_body)
    except ValueError:
        return bad_request(errorMessage='Error parsing request body, Expected JSON.')

    method = event['httpMethod']
    return submit_dataset(body_dict, method)


if __name__ == '__main__':
    event = {
        "httpMethod": "POST",
        "body": json.dumps({
            "dataset": {
                "id": "test-wic",
                "name": "my test dataset"
            },
            "cohort": {
                "id": "test-wic",
                "name": "GCAT Genomes for Life",
                "cohortType": "study-defined"
            },
            "individuals": [
                {
                    "id": "some id",
                    "sex": {
                        "id": "ga4gh:GA.01234abcde"
                    },
                    "sampleName": "some sampleName"
                }
            ],
            "biosamples": [
                {
                    "id": "biosample kind of a id",
                    "biosampleStatus": {
                        "id": "ga4gh:GA.01234abcde"
                    },
                    "sampleOriginType": {
                        "id": "DUO:0000004"
                    },
                    "sampleName": "biosample kind of a sampleName"
                }
            ],
            "runs": [
                {
                    "id": "runs kind of a id",
                    "biosampleId": "biosample kind of a id",
                    "runDate": "2021-10-18"
                }
            ],
            "analyses": [
                {
                    "id": "analyses kind of a id",
                    "analysisDate": "2021-10-17",
                    "pipelineName": "Pipeline-panel-0001-v1"
                }
            ],
            "assemblyId": "GRCH38",
            "vcfLocations": [
                "s3://simulationexperiments/test-vcfs/100.chr5.80k.vcf.gz"
            ],
            "vcfGroups": [
                [
                    "s3://simulationexperiments/test-vcfs/100.chr5.80k.vcf.gz"
                ]
            ]
        })
    }

    lambda_handler(event, {})