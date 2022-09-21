import random
import os

from tqdm import tqdm

from athena.dataset import Dataset
from athena.cohort import Cohort
from athena.individual import Individual
from athena.biosample import Biosample
from athena.run import Run
from athena.analysis import Analysis
from dynamodb.datasets import Dataset as DynamoDataset, VcfChromosomeMap
from utils import get_vcf_chromosomes, upload_batch_s3, get_samples


METADATA_BUCKET = os.environ['METADATA_BUCKET']


def get_radnom_dataset(id, vcfLocations, vcfChromosomeMap, seed=0):
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
    dynamo_item.assemblyId = random.choice(["GRCH38", "GRCH37", "HG16"])
    dynamo_item.vcfGroups = [vcfLocations]
    dynamo_item.vcfLocations = vcfLocations
    dynamo_item.vcfChromosomeMap = vcfChromosomeMap

    return item, dynamo_item


def get_radnom_cohort(id, seed=0):
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


def get_radnom_individual(id, datasetId, cohortId, seed=0):
    random.seed(seed)

    item= Individual(id=id, datasetId=datasetId, cohortId=cohortId)
    item.diseases = []
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
            "id": "NCIT:C126535",
            "label": "Australian"
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
    item.exposures = []
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
        }
    ])
    item.info = {}
    item.interventionsOrProcedures = []
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
        }
    ])
    item.treatments = []

    return item


def get_radnom_biosample(id, datasetId, cohortId, individualId, seed=0):
    random.seed(seed)

    item = Biosample(id=id, datasetId=datasetId, cohortId=cohortId, individualId=individualId)
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


def get_radnom_run(id, datasetId, cohortId, individualId, biosampleId, seed=0):
    random.seed(seed)

    item = Run(id=id, datasetId=datasetId, cohortId=cohortId, individualId=individualId, biosampleId=biosampleId)
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


def get_radnom_analysis(id, datasetId, cohortId, individualId, biosampleId, runId, seed=0):
    random.seed(seed)

    item = Analysis(id=id, datasetId=datasetId, cohortId=cohortId, individualId=individualId, biosampleId=biosampleId, runId=runId)
    item.aligner = random.choice(["bwa-0.7.8", "minimap2", "bowtie"])
    item.analysisDate = f"{random.randint(2018, 2022)}-{random.randint(1, 12)}-{random.randint(1, 28)}"
    item.pipelineName = f"pipeline {random.randint(1, 5)}"
    item.pipelineRef = "Example"
    item.variantCaller = random.choice(["GATK4.0", "SoapSNP", "kmer2snp"])

    return item


if __name__ == "__main__":
    dynamo_items = []
    datasets = []

    # datasets
    for n, line in enumerate(open('vcf.txt')):
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
            dataset, dynamo_item = get_radnom_dataset(id, vcfs, vcfChromosomeMap, seed=id)
            dynamo_item.sampleCount = len(samples)
            dynamo_item.sampleNames = samples
            dynamo_items.append(dynamo_item)
            datasets.append(dataset)

    # upload datasets
    key = f'combined-datasets'
    path = f's3://{METADATA_BUCKET}/datasets/{key}'
    upload_batch_s3((Dataset, datasets, path))

    with DynamoDataset.batch_write() as batch:
        for item in tqdm(dynamo_items, desc="Writing datasets to DynamoDB"):
            batch.save(item)
    datasets = []

    # cohorts
    cohorts = []
    for dataset in tqdm(dynamo_items, desc="Simulating cohorts"):
        id = dataset.id
        cohort = get_radnom_cohort(id=id, seed=id)
        cohorts.append(cohort)
    key = f'combined-cohort'
    path = f's3://{METADATA_BUCKET}/cohorts/{key}'
    upload_batch_s3((Cohort, cohorts, path))
    cohorts = []

    individuals = []
    for dataset in tqdm(dynamo_items, desc="Simulating individuals"):
        id = dataset.id
        nosamples = dataset.sampleCount
        for itr in range(nosamples):
            individual = get_radnom_individual(id=f'{id}-{itr}', datasetId=id, cohortId=id, seed=f'{id}-{itr}')
            individuals.append(individual)
    key = f'combined-individuals'
    path = f's3://{METADATA_BUCKET}/individuals/{key}'
    upload_batch_s3(((Individual, individuals, path)))
    individuals = []

    # biosamples
    biosamples = []
    for dataset in tqdm(dynamo_items, desc="Simulating biosamples"):
        id = dataset.id
        nosamples = dataset.sampleCount
        for itr in range(nosamples):
            biosample = get_radnom_biosample(id=f'{id}-{itr}', datasetId=id, cohortId=id, individualId=f'{id}-{itr}', seed=f'{id}-{itr}')
            biosamples.append(biosample)
    key = f'combined-biosamples'
    path = f's3://{METADATA_BUCKET}/biosamples/{key}'
    upload_batch_s3((Biosample, biosamples, path))
    biosamples = []

    # runs
    runs = []
    for dataset in tqdm(dynamo_items, desc="Simulating runs"):
        id = dataset.id
        nosamples = dataset.sampleCount
        for itr in range(nosamples):
            run = get_radnom_run(id=f'{id}-{itr}', datasetId=id, cohortId=id, individualId=f'{id}-{itr}', biosampleId=f'{id}-{itr}', seed=f'{id}-{itr}')
            runs.append(run)
    key = f'combined-runs'
    path = f's3://{METADATA_BUCKET}/runs/{key}'
    upload_batch_s3((Run, runs, path))
    runs = []

    # analyses
    analyses = []
    for dataset in tqdm(dynamo_items, desc="Simulating analyses"):
        id = dataset.id
        nosamples = dataset.sampleCount
        for itr in range(nosamples):
            analysis = get_radnom_analysis(id=f'{id}-{itr}', datasetId=id, cohortId=id, individualId=f'{id}-{itr}', biosampleId=f'{id}-{itr}', runId=f'{id}-{itr}', seed=f'{id}-{itr}')
            analyses.append(analysis)

    key = f'combined-analyses'
    path = f's3://{METADATA_BUCKET}/analyses/{key}'
    upload_batch_s3((Analysis, analyses, path))
    analyses = []            
