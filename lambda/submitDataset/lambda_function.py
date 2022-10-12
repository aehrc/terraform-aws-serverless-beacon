import json
import os
import subprocess
from typing import List

from jsonschema import Draft202012Validator, RefResolver
import jsons
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
    datasetId = attributes.get('datasetId', None)
    cohortId = attributes.get('cohortId', None)
    messages = []

    if datasetId:
        item = DynamoDataset(datasetId)
        item.assemblyId = attributes.get('assemblyId', '')
        item.vcfLocations = attributes.get('vcfLocations', [])
        item.vcfGroups = attributes.get('vcfGroups', [item.vcfLocations])
        for vcf in set(item.vcfLocations):
            chroms = get_vcf_chromosomes(vcf)
            vcfm = VcfChromosomeMap()
            vcfm.vcf = vcf
            vcfm.chromosomes = chroms
            item.vcfChromosomeMap.append(vcfm)

        print(f"Putting item in table: {item.to_json()}")
        item.save()
        messages.append("Added dataset info")
        # dataset information
        json_dataset = attributes.get('dataset', None)
        if json_dataset:
            dataset = jsons.load(json_dataset, Dataset)
            dataset.id = datasetId
            dataset._assemblyId = item.assemblyId 
            dataset._vcfLocations = item.vcfLocations 
            dataset._vcfChromosomeMap = [vcfm.attribute_values for vcfm in item.vcfChromosomeMap]
            dataset.createDateTime = str(item.createDateTime)
            dataset.updateDateTime = str(item.updateDateTime)
            Dataset.upload_array([dataset])
            messages.append("Added dataset metadata")

    if datasetId and cohortId:


        individuals = jsons.default_list_deserializer(attributes.get('individuals', []), List[Individual])
        biosamples = jsons.default_list_deserializer(attributes.get('biosamples', []), List[Biosample])
        runs = jsons.default_list_deserializer(attributes.get('runs', []), List[Run])
        analyses = jsons.default_list_deserializer(attributes.get('analyses', []), List[Analysis])
        
        # setting dataset id
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
            Individual.upload_array(individuals)
            messages.append("Added individuals")
        if len(biosamples) > 0: 
            Biosample.upload_array(biosamples)
            messages.append("Added biosamples")
        if len(runs) > 0:
            Run.upload_array(runs)
            messages.append("Added runs")
        if len(analyses) > 0: 
            Analysis.upload_array(analyses)
            messages.append("Added analyses")
    
    if cohortId:
        # cohort information
        json_cohort = attributes.get('cohort', None)
        if json_cohort:
            cohort = jsons.load(json_cohort, Cohort)
            cohort.id = cohortId
            Cohort.upload_array([cohort])
            messages.append("Added cohorts")

    aws_lambda.invoke(
        FunctionName=INDEXER_LAMBDA,
        InvocationType='Event',
        Payload=jsons.dumps(dict()),
    )

    return messages


def submit_dataset(body_dict, method):
    new = method == 'POST'
    validation_errors = validate_request(body_dict, new)
    completed = []
    pending = []

    if validation_errors:
        print()
        print(', '.join(validation_errors))
        return bad_request(errorMessage=', '.join(validation_errors))

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
        completed += create_dataset(body_dict)
    else:
        update_dataset(body_dict)
    
    if summarise:
        summarise_dataset(body_dict['datasetId'])
        pending.append('Summarising')

    return bundle_response(200, { 'Completed': completed, 'Running': pending })


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
    datasetId = attributes['datasetId']
    item = DynamoDataset.get(datasetId)
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
        validator = Draft202012Validator(newSchema, resolver=resolveNew)
    else:
        validator = Draft202012Validator(updateSchema, resolver=resolveUpdate)

    errors = []
    
    for error in sorted(validator.iter_errors(parameters), key=lambda e: e.path):
        error_message = f'{error.message} '
        for part in list(error.path):
            error_message += f'/{part}'
        errors.append(error_message)
    return errors


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
    pass
