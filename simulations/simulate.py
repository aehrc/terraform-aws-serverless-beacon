from collections import defaultdict
import random
import os
import sys
import boto3
import pyorc
import re
import threading
import multiprocessing
from glob import glob
import concurrent.futures

from tqdm import tqdm
from smart_open import open as sopen
import jsons

from athena.dataset import Dataset
from athena.cohort import Cohort
from athena.individual import Individual
from athena.biosample import Biosample
from athena.run import Run
from athena.analysis import Analysis
from dynamodb.datasets import Dataset as DynamoDataset, VcfChromosomeMap
from dynamodb.ontologies import Ontology, Descendants, Anscestors
from utils import get_vcf_chromosomes, get_samples, get_writer, write_local, upload_local


METADATA_BUCKET = os.environ['METADATA_BUCKET']
pattern = re.compile(f'^\\w[^:]+:.+$')
s3 = boto3.client('s3')
threads_count = 56
terms_cache_header = 'struct<kind:string,id:string,term:string,label:string,type:string>'
datasets_path = './tmp-datasets'
cohorts_path = './tmp-cohorts'
individuals_path = './tmp-individuals'
biosamples_path = './tmp-biosamples'
runs_path = './tmp-runs'
analyses_path = './tmp-analyses'


def get_random_dataset(id, vcfLocations, vcfChromosomeMap, seed=0):
    random.seed(seed)

    item = Dataset(id=id)
    item.createDateTime = random.choice([
        "1999-08-05T17:21:00+01:00",
        "2002-05-21T02:37:00-08:00",
        "2019-11-21T02:37:00-08:00",
        "2020-02-21T02:37:00-08:00",
        "2021-03-21T02:37:00-08:00",
        "2022-10-21T02:37:00-08:00"
    ])
    item.dataUseConditions = random.choice([
        {
            "duoDataUse": [
                {
                    "id": "DUO:0000007",
                    "label": "disease specific research",
                    "modifiers": [
                        {
                            "id": "EFO:0001645",
                            "label": "coronary artery disease"
                        }
                    ],
                    "version": "17-07-2016"
                }
            ]
        },
        {
            "duoDataUse": [
                {
                    "id": "DUO:0000004",
                    "label": "no restriction",
                    "version": "2022-03-23"
                }
            ]
        }
    ])
    item.description = random.choice([
        "Simulation set 0.",
        "Simulation set 1.",
        "Simulation set 2.",
        "Simulation set 3."
    ])
    item.externalUrl = random.choice([
        "http://example.org/wiki/Main_Page",
        "http://example.com/vcf/vcfs",
        "http://example.net/var/variants",
        "http://example.io/data/data"
    ])
    item.info = {}
    item.name = random.choice([
        "Dataset with synthetic data",
        "Dataset with simulated data",
        "Dataset with fake data",
    ])
    item.updateDateTime = random.choice([
        "2022-08-05T17:21:00+01:00",
        "2021-09-21T02:37:00-08:00"
    ])
    item.version = random.choice([
        "v1.1",
        "v2.1",
        "v3.1",
    ])

    dynamo_item = DynamoDataset(id)
    dynamo_item.assemblyId = random.choice(["GRCH38"])
    dynamo_item.vcfGroups = [vcfLocations]
    dynamo_item.vcfLocations = vcfLocations
    dynamo_item.vcfChromosomeMap = vcfChromosomeMap

    item._assemblyId = dynamo_item.assemblyId
    item._vcfLocations = dynamo_item.vcfLocations
    item._vcfChromosomeMap = [
        item.attribute_values for item in dynamo_item.vcfChromosomeMap]

    return item, dynamo_item


def get_random_cohort(id, seed=0):
    random.seed(seed)

    item = Cohort(id=id)
    item.cohortDataTypes = [
        random.choice([
            {
                "id": "OGMS:0000015",
                "label": "clinical history"
            },
            {
                "id": "OBI:0000070",
                "label": "genotyping assay"
            },
            {
                "id": "OMIABIS:0000060",
                "label": "survey data"
            }
        ]) for _ in range(2)
    ]
    item.cohortDesign = {
        "id": random.choice(
            [
                "ga4gh:GA.01234abcde",
                "DUO:0000004",
                "orcid:0000-0003-3463-0775",
                "PMID:15254584"
            ]
        )
    }
    item.cohortSize = -1
    item.cohortType = random.choice([
        "study-defined",
        "beacon-defined",
        "user-defined"
    ])
    item.collectionEvents = {}
    item.exclusionCriteria = {}
    item.inclusionCriteria = {}
    item.name = random.choice([
        "Wellcome Trust Case Control Consortium",
        "GCAT Genomes for Life",
        "ACGT example organisation"
    ])

    return item


def get_random_individual(id, datasetId, cohortId, seed=0):
    random.seed(seed)

    item = Individual(id=id, datasetId=datasetId, cohortId=cohortId)
    item.diseases = random.sample(
        [
            {
                "diseaseCode": {
                    "id": "EFO:0000400",
                    "label": "insulin-dependent diabetes mellitus"
                }
            },
            {
                "diseaseCode": {
                    "id": "MONDO:0005090",
                    "label": "schizophrenia"
                }
            },
            {
                "diseaseCode": {
                    "id": "EFO:0000249",
                    "label": "alzheimer's disease"
                }
            },
            {
                "diseaseCode": {
                    "id": "MONDO:0005812",
                    "label": "influenza due to certain identified influenza virus"
                }
            }
        ], random.randint(0, 3))
    item.ethnicity = random.choice([
        {
            "id": "NCIT:C42331",
            "label": "African"
        },
        {
            "id": "NCIT:C41260",
            "label": "Asian"
        },
        {
            "id": "SNOMED:413582008",
            "label": "Asian race (racial group)"
        },
        {
            "id": "NCIT:C126535",
            "label": "Australian"
        },
        {
            "id": "SNOMED:413464008",
            "label": "African race (racial group)"
        },
        {
            "id": "NCIT:C43851",
            "label": "European"
        },
        {
            "id": "NCIT:C77812",
            "label": "North American"
        },
        {
            "id": "NCIT:C126531",
            "label": "Latin American"
        },
        {
            "id": "NCIT:C104495",
            "label": "Other race"
        }
    ])
    item.exposures = random.sample([
        {
            "exposureCode": {
                "id": "NCIT:C94596"
            }
        },
        {
            "exposureCode": {
                "id": "NCIT:C50738"
            }
        },
        {
            "exposureCode": {
                "id": "NCIT:C156623"
            }
        },
        {
            "exposureCode": {
                "id": "NCIT:C94492"
            }
        },
        {
            "exposureCode": {
                "id": "NCIT:C154864"
            }
        }
    ], random.randint(0, 2))
    item.geographicOrigin = random.choice([
        {
            "id": "GAZ:00002955",
            "label": "Slovenia"
        },
        {
            "id": "GAZ:00002459",
            "label": "United States of America"
        },
        {
            "id": "GAZ:00316959",
            "label": "Municipality of El Masnou"
        },
        {
            "id": "GAZ:00000460",
            "label": "Eurasia"
        },
        {
            "id": "SNOMED:223506007",
            "label":"Indian subcontinent (geographic location)"
        }
    ])
    item.info = {}
    item.interventionsOrProcedures = random.sample([
        {
            "procedureCode": {
                "id": "NCIT:C64264"
            }
        },
        {
            "procedureCode": {
                "id": "NCIT:C64263"
            }
        },
        {
            "procedureCode": {
                "id": "NCIT:C93025"
            }
        },
        {
            "procedureCode": {
                "id": "NCIT:C79426"
            }
        }
    ], random.randint(0, 2))
    item.karyotypicSex = random.choice([
        "UNKNOWN_KARYOTYPE",
        "XX",
        "XY",
        "XO",
        "XXY",
        "XXX",
        "XXYY",
        "XXXY",
        "XXXX",
        "XYY",
        "OTHER_KARYOTYPE"
    ])
    item.measures = []
    item.pedigrees = []
    item.phenotypicFeatures = []
    item.sex = random.choice([
        {
            "id": "NCIT:C16576",
            "label": "female"
        },
        {
            "id": "NCIT:C20197",
            "label": "male"
        },
        {
            "id": "NCIT:C1799",
            "label": "unknown"
        },
        {
            "id": "SNOMED:223589002",
            "label": "Indonesia (geographic location)"
        }
    ])
    item.treatments = []

    return item


def get_random_biosample(id, datasetId, cohortId, individualId, seed=0):
    random.seed(seed)

    item = Biosample(id=id, datasetId=datasetId,
                     cohortId=cohortId, individualId=individualId)
    item.biosampleStatus = random.choice([
        {
            "id": "EFO:0009654",
            "label": "reference sample"
        },
        {
            "id": "EFO:0009655",
            "label": "abnormal sample"
        },
        {
            "id": "EFO:0009656",
            "label": "neoplastic sample"
        },
        {
            "id": "EFO:0010941",
            "label": "metastasis sample"
        },
        {
            "id": "EFO:0010942",
            "label": "primary tumor sample"
        },
        {
            "id": "EFO:0010943",
            "label": "recurrent tumor sample"
        }
    ])
    item.collectionDate = random.choice([
        "2021-04-23",
        "2022-04-23",
        "2019-04-23",
        "2018-04-23",
        "2015-04-23"
    ])
    item.collectionMoment = random.choice([
        "P32Y6M1D",
        "P7D"
    ])
    item.diagnosticMarkers = []
    item.histologicalDiagnosis = random.choice([
        {},
        {
            "id": "NCIT:C3778",
            "label": "Serous Cystadenocarcinoma"
        }
    ])
    item.measurements = []
    item.obtentionProcedure = random.choice([
        {},
        {
            "code": {
                "id": "NCIT:C15189",
                "label": "biopsy"
            }
        },
        {
            "code": {
                "id": "NCIT:C157179",
                "label": "FGFR1 Mutation Analysis"
            }
        }])
    item.pathologicalStage = random.choice([
        {},
        {},
        {
            "id": "NCIT:C27977",
            "label": "Stage IIIA"
        }
    ])
    item.pathologicalTnmFinding = random.choice([
        {},
        {
            "id": "NCIT:C48725",
            "label": "T2a Stage Finding"
        },
        {
            "id": "NCIT:C48709",
            "label": "N1c Stage Finding"
        },
        {
            "id": "NCIT:C48699",
            "label": "M0 Stage Finding"
        }])
    item.phenotypicFeatures = []
    item.sampleOriginDetail = random.choice([
        {},
        {
            "id": "UBERON:0000474",
            "label": "female reproductive system"
        },
        {
            "id": "BTO:0002181",
            "label": "HEK-293T cell"
        },
        {
            "id": "OBI:0002606",
            "label": "nasopharyngeal swab specimen"
        }
    ])
    item.sampleOriginType = random.choice([
        {},
        {
            "id": "OBI:0001479",
            "label": "specimen from organism"
        },
        {
            "id": "OBI:0001876",
            "label": "cell culture"
        },
        {
            "id": "OBI:0100058",
            "label": "xenograft"
        }
    ])
    item.sampleProcessing = random.choice([
        {},
        {
            "id": "EFO:0009129",
            "label": "mechanical dissociation"
        }
    ])
    item.sampleStorage = {},
    item.tumorGrade = random.choice([
        {},
        {
            "id": "NCIT:C28080",
            "label": "Grade 3a"
        }
    ])
    item.tumorProgression = random.choice([
        {},
        {
            "id": "NCIT:C84509",
            "label": "Primary Malignant Neoplasm"
        },
        {
            "id": "NCIT:C4813",
            "label": "Recurrent Malignant Neoplasm"
        }
    ])
    item.info = []
    item.notes = []

    return item


def get_random_run(id, datasetId, cohortId, individualId, biosampleId, seed=0):
    random.seed(seed)

    item = Run(id=id, datasetId=datasetId, cohortId=cohortId,
               individualId=individualId, biosampleId=biosampleId)
    item.libraryLayout = "PAIRED"
    item.librarySelection = "RANDOM"
    item.librarySource = random.choice(
        [
            {
                "id": "GENEPIO:0001969",
                "label": "other library source"
            },
            {
                "id": "GENEPIO:0001966",
                "label": "genomic source"
            }
        ]
    )
    item.libraryStrategy = "WGS"
    idx = random.choice([0, 1, 2])
    item.platform = ["Illumina", "PacBio", "NanoPore"][idx]
    item.platformModel = [
        {
            "id": "OBI:0002048",
            "label": "Illumina HiSeq 3000"
        },
        {
            "id": "OBI:0002012",
            "label": "PacBio RS II"
        },
        {
            "id": "OBI:0002750",
            "label": "Oxford Nanopore MinION"
        }
    ][idx]
    item.runDate = random.choice(["2021-10-18", "2022-08-08", "2018-01-01"])

    return item


def get_random_analysis(id, datasetId, cohortId, individualId, biosampleId, runId, vcfSampleId, seed=0):
    random.seed(seed)

    item = Analysis(id=id, datasetId=datasetId, cohortId=cohortId, individualId=individualId,
                    biosampleId=biosampleId, vcfSampleId=vcfSampleId, runId=runId)
    item.aligner = random.choice(["bwa-0.7.8", "minimap2", "bowtie"])
    item.analysisDate = f"{random.randint(2018, 2022)}-{random.randint(1, 12)}-{random.randint(1, 28)}"
    item.pipelineName = f"pipeline {random.randint(1, 5)}"
    item.pipelineRef = "Example"
    item.variantCaller = random.choice(["GATK4.0", "SoapSNP", "kmer2snp"])

    return item


def clean_files(bucket, prefix):
    has_more = True
    pbar = tqdm(desc='Cleaning Files')
    while has_more:
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        files_to_delete = []
        for object in response.get('Contents', []):
            files_to_delete.append({"Key": object["Key"]})
        s3.delete_objects(
            Bucket=bucket, 
            Delete={ "Objects": files_to_delete })
        pbar.update(len(files_to_delete))
        has_more = response['IsTruncated']


def clean():
    with DynamoDataset.batch_write() as batch:
        for dynamo_item in tqdm(DynamoDataset.scan(), desc='Cleaning Dataset'):
            batch.delete(dynamo_item)

    with Ontology.batch_write() as batch:
        for dynamo_item in tqdm(Ontology.scan(), desc='Cleaning Ontology'):
            batch.delete(dynamo_item)

    with Anscestors.batch_write() as batch:
        for dynamo_item in tqdm(Anscestors.scan(), desc='Cleaning Anscestors'):
            batch.delete(dynamo_item)

    with Descendants.batch_write() as batch:
        for dynamo_item in tqdm(Descendants.scan(), desc='Cleaning Descendants'):
            batch.delete(dynamo_item)

    clean_files(METADATA_BUCKET, '')


def extract_terms(array):
    for item in array:
        if type(item) == dict:
            label = item.get('label', '')
            typ = item.get('type', 'string')
            for key, value in item.items():
                if type(value) == str:
                    if key == "id" and pattern.match(value):
                        yield value, label, typ
                if type(value) == dict:
                    yield from extract_terms([value])
                elif type(value) == list:
                    yield from extract_terms(value)
        if type(item) == str:
            continue
        elif type(item) == list:
            yield from extract_terms(item)


def simulate_datasets_cohorts():
    dynamo_items = []
    dataset_samples = dict()
    path_datasets = f'{datasets_path}.orc'
    path_datasets_terms = f'{datasets_path}-terms.orc'
    path_cohorts = f'{cohorts_path}.orc'
    path_cohorts_terms = f'{cohorts_path}-terms.orc'

    # datasets
    terms_file = open(path_datasets_terms, 'wb+')
    terms_writer = pyorc.Writer(terms_file, terms_cache_header)
    file, writer = get_writer(Dataset, path_datasets)

    for n, line in enumerate(open('vcf.txt')):
        if line[0] == '#':
            continue
        data = line.strip().split(' ')
        multiplier = int(data[0])
        vcfs = data[1:]
        vcfChromosomeMap = []

        samples = get_samples(vcfs[0])

        # vcf chromosomes
        for vcf in set(vcfs):
            chroms = get_vcf_chromosomes(vcf)
            vcfm = VcfChromosomeMap()
            vcfm.vcf = vcf
            vcfm.chromosomes = chroms
            vcfChromosomeMap.append(vcfm)

        for m in tqdm(range(multiplier), desc="Simulating datasets"):
            id = f'{n}-{m}'
            dataset, dynamo_item = get_random_dataset(
                id, vcfs, vcfChromosomeMap, seed=id)
            
            for term, label, typ in extract_terms([jsons.dump(dataset)]):
                terms_writer.write(('datasets', dataset.id, term, label, typ))
            
            dynamo_item.sampleCount = len(samples)
            # dynamo_item.sampleNames = samples
            dynamo_item.sampleNames = ['None']
            dataset_samples[id] = samples
            dynamo_items.append(dynamo_item)
            write_local(Dataset, dataset, writer)
    writer.close()
    file.close()
    terms_writer.close()
    terms_file.close()

    with DynamoDataset.batch_write() as batch:
        for item in tqdm(dynamo_items, desc="Writing datasets to DynamoDB"):
            batch.save(item)

    # cohorts
    terms_file = open(path_cohorts_terms, 'wb+')
    terms_writer = pyorc.Writer(terms_file, terms_cache_header)
    file, writer = get_writer(Cohort, path_cohorts)

    for dataset in tqdm(dynamo_items, desc="Simulating cohorts"):
        id = dataset.id
        cohort = get_random_cohort(id=id, seed=id)

        for term, label, typ in extract_terms([jsons.dump(cohort)]):
                terms_writer.write(('cohorts', cohort.id, term, label, typ))

        write_local(Cohort, cohort, writer)
    
    writer.close()
    file.close()
    terms_writer.close()
    terms_file.close()

    return dynamo_items, dataset_samples

    
def simulate_individuals(dynamo_items):
    def runner(thread_id):
        idx = 1
        thread_path = f'./{individuals_path}-{thread_id}-{idx}.orc'
        thread_terms_path = f'./{individuals_path}-terms-{thread_id}.orc'
        terms_file = open(thread_terms_path, 'wb+')
        terms_writer = pyorc.Writer(terms_file, terms_cache_header)
        file, writer = get_writer(Individual, thread_path)
        pbar = tqdm(desc=f'Individuals thread - {thread_id}', position=thread_id)

        for n, dataset in enumerate(dynamo_items):
            if n % threads_count != thread_id:
                continue
            
            id = dataset.id
            nosamples = dataset.sampleCount
            
            for itr in range(nosamples):
                individual = get_random_individual(
                    id=f'{id}-{itr}', datasetId=id, cohortId=id, seed=f'{id}-{itr}')
                
                for term, label, typ in extract_terms([jsons.dump(individual)]):
                    terms_writer.write(('individuals', individual.id, term, label, typ))
                
                write_local(Individual, individual, writer)
                idx += 1
                
                if idx % 1000000 == 0:
                    writer.close()
                    file.close()
                    thread_path = f'./{individuals_path}-{thread_id}-{idx}.orc'
                    file, writer = get_writer(Individual, thread_path)
                pbar.update()

        writer.close()
        file.close()
        terms_writer.close()
        terms_file.close()
        pbar.close()
        

    threads = [multiprocessing.Process(target=runner, args=(thread_id,)) for thread_id in range(threads_count)]
    [thread.start() for thread in threads]
    [thread.join() for thread in threads]
    print()


def simulate_biosamples(dynamo_items):
    def runner(thread_id):
        idx = 1
        thread_path = f'./{biosamples_path}-{thread_id}-{idx}.orc'
        thread_terms_path =f'./{biosamples_path}-terms-{thread_id}.orc'
        terms_file = open(thread_terms_path, 'wb+')
        terms_writer = pyorc.Writer(terms_file, terms_cache_header)
        file, writer = get_writer(Biosample, thread_path)
        pbar = tqdm(desc=f'Biosamples thread - {thread_id}', position=thread_id)

        for n, dataset in enumerate(dynamo_items):
            if n % threads_count != thread_id:
                continue
            
            id = dataset.id
            nosamples = dataset.sampleCount
            
            for itr in range(nosamples):
                biosample = get_random_biosample(
                    id=f'{id}-{itr}', datasetId=id, cohortId=id, individualId=f'{id}-{itr}', seed=f'{id}-{itr}')
                
                for term, label, typ in extract_terms([jsons.dump(biosample)]):
                    terms_writer.write(('biosamples', biosample.id, term, label, typ))

                write_local(Biosample, biosample, writer)
                idx += 1
                
                if idx % 1000000 == 0:
                    writer.close()
                    file.close()
                    thread_path = f'./{biosamples_path}-{thread_id}-{idx}.orc'
                    file, writer = get_writer(Biosample, thread_path)
                
                pbar.update()

        writer.close()
        file.close()
        terms_writer.close()
        terms_file.close()
        pbar.close()

    threads = [multiprocessing.Process(target=runner, args=(thread_id,)) for thread_id in range(threads_count)]
    [thread.start() for thread in threads]
    [thread.join() for thread in threads]
    print()


def simulate_runs(dynamo_items):
    def runner(thread_id):
        idx = 1
        thread_path = f'./{runs_path}-{thread_id}-{idx}.orc'
        thread_terms_path =f'./{runs_path}-terms-{thread_id}.orc'
        terms_file = open(thread_terms_path, 'wb+')
        terms_writer = pyorc.Writer(terms_file, terms_cache_header)
        file, writer = get_writer(Run, thread_path)
        pbar = tqdm(desc=f'Runs thread - {thread_id}', position=thread_id)

        for n, dataset in enumerate(dynamo_items):
            if n % threads_count != thread_id:
                continue

            id = dataset.id
            nosamples = dataset.sampleCount
            
            for itr in range(nosamples):
                run = get_random_run(id=f'{id}-{itr}', datasetId=id, cohortId=id,
                                    individualId=f'{id}-{itr}', biosampleId=f'{id}-{itr}', seed=f'{id}-{itr}')
                
                for term, label, typ in extract_terms([jsons.dump(run)]):
                    terms_writer.write(('runs', run.id, term, label, typ))

                write_local(Run, run, writer)
                idx += 1
                
                if idx % 1000000 == 0:
                    writer.close()
                    file.close()
                    thread_path = f'./{runs_path}-{thread_id}-{idx}.orc'
                    file, writer = get_writer(Run, thread_path)

                pbar.update()

        writer.close()
        file.close()
        terms_writer.close()
        terms_file.close()
        pbar.close()

    threads = [multiprocessing.Process(target=runner, args=(thread_id,)) for thread_id in range(threads_count)]
    [thread.start() for thread in threads]
    [thread.join() for thread in threads]
    print()


def simulate_analyses(dynamo_items, dataset_samples):
    def runner(thread_id):
        idx = 1
        thread_path = f'./{analyses_path}-{thread_id}-{idx}.orc'
        thread_terms_path =f'./{analyses_path}-terms-{thread_id}.orc'
        terms_file = open(thread_terms_path, 'wb+')
        terms_writer = pyorc.Writer(terms_file, terms_cache_header)
        file, writer = get_writer(Analysis, thread_path)
        pbar = tqdm(desc=f'Analyses thread - {thread_id}', position=thread_id)

        for n, dataset in enumerate(dynamo_items):
            if n % threads_count != thread_id:
                continue

            id = dataset.id
            nosamples = dataset.sampleCount

            for itr in range(nosamples):
                analysis = get_random_analysis(
                    id=f'{id}-{itr}', 
                    datasetId=id, 
                    cohortId=id, 
                    individualId=f'{id}-{itr}',
                    biosampleId=f'{id}-{itr}', 
                    runId=f'{id}-{itr}', 
                    # vcfSampleId=dataset.sampleNames[itr], 
                    vcfSampleId=dataset_samples[id][itr], 
                    seed=f'{id}-{itr}')
                
                for term, label, typ in extract_terms([jsons.dump(analysis)]):
                    terms_writer.write(('analyses', analysis.id, term, label, typ))

                write_local(Analysis, analysis, writer)
                idx += 1
                if idx % 1000000 == 0:
                    writer.close()
                    file.close()
                    thread_path = f'./{analyses_path}-{thread_id}-{idx}.orc'
                    file, writer = get_writer(Analysis, thread_path)

                pbar.update()

        writer.close()
        file.close()
        terms_writer.close()
        terms_file.close()
        pbar.close()

    threads = [multiprocessing.Process(target=runner, args=(thread_id,)) for thread_id in range(threads_count)]
    [thread.start() for thread in threads]
    [thread.join() for thread in threads]
    print()


def simulate():
    dynamo_items, dataset_samples = simulate_datasets_cohorts()
    print('Simulating individuals', flush=True)
    simulate_individuals(dynamo_items)
    print('Simulating biosamples', flush=True)
    simulate_biosamples(dynamo_items)
    print('Simulating runs', flush=True)
    simulate_runs(dynamo_items)
    print('Simulating analyses', flush=True)
    simulate_analyses(dynamo_items, dataset_samples)
    print(flush=True, end='')


def upload():
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=threads_count)

    # upload datasets
    pool.submit(upload_local, f'{datasets_path}.orc', f's3://{METADATA_BUCKET}/datasets/combined-datasets.orc')
    pool.submit(upload_local, f'{datasets_path}-terms.orc', f's3://{METADATA_BUCKET}/terms-cache/datasets.orc')

    # upload cohorts
    pool.submit(upload_local, f'{cohorts_path}.orc', f's3://{METADATA_BUCKET}/cohorts/combined-cohorts.orc')
    pool.submit(upload_local, f'{cohorts_path}-terms.orc', f's3://{METADATA_BUCKET}/terms-cache/cohorts.orc')
    
    # upload individuals
    for thread in range(threads_count):
        pool.submit(upload_local, f'./{individuals_path}-terms-{thread}.orc', f's3://{METADATA_BUCKET}/terms-cache/individuals-{thread}.orc')
        pool.submit(upload_local, f'./{biosamples_path}-terms-{thread}.orc', f's3://{METADATA_BUCKET}/terms-cache/biosamples-{thread}.orc')
        pool.submit(upload_local, f'./{runs_path}-terms-{thread}.orc', f's3://{METADATA_BUCKET}/terms-cache/runs-{thread}.orc')
        pool.submit(upload_local, f'./{analyses_path}-terms-{thread}.orc', f's3://{METADATA_BUCKET}/terms-cache/analyses-{thread}.orc')
        
        for file in glob(f'{individuals_path}-{thread}-*'):
            idx = file.split('/')[-1].replace('.orc', '')
            pool.submit(upload_local, file, f's3://{METADATA_BUCKET}/individuals/individuals-{thread}-{idx}.orc')

        for file in glob(f'{biosamples_path}-{thread}-*'):
            idx = file.split('/')[-1].replace('.orc', '')
            pool.submit(upload_local, file, f's3://{METADATA_BUCKET}/biosamples/biosamples-{thread}-{idx}')
        
        for file in glob(f'{runs_path}-{thread}-*'):
            idx = file.split('/')[-1].replace('.orc', '')
            pool.submit(upload_local, file, f's3://{METADATA_BUCKET}/runs/runs-{thread}-{idx}')
        
        for file in glob(f'{analyses_path}-{thread}-*'):
            idx = file.split('/')[-1].replace('.orc', '')
            pool.submit(upload_local, file, f's3://{METADATA_BUCKET}/analyses/analyses-{thread}-{idx}')
    pool.shutdown()


if __name__ == "__main__":
    if not len(sys.argv) == 2 or sys.argv[1] not in ('simulate', 'upload', 'clean'):
        print('Usage: \n\t$ python simulate.py MODE [simulate|upload|clean]\n')
        sys.exit(1)
    print('START')
    if sys.argv[1] == 'simulate':
        simulate()
    elif sys.argv[1] == 'upload':
        upload()
    else:
        clean()
    print('END')
