import concurrent.futures
import multiprocessing
from glob import glob
import random
import shutil
import json
import sys
import os
import re

from tqdm import tqdm
import pyorc
import boto3
import jsons

from shared.athena import Dataset, Cohort, Individual, Biosample, Run, Analysis
from shared.dynamodb import (
    Dataset as DynamoDataset,
    VcfChromosomeMap,
    Ontology,
    Descendants,
    Anscestors,
    VariantQuery,
    VariantResponse,
)
from shared.utils import get_vcf_chromosomes
from utils import (
    get_samples,
    get_writer,
    write_local,
    upload_local,
)


ATHENA_METADATA_BUCKET = os.environ["ATHENA_METADATA_BUCKET"]

pattern = re.compile(f"^\\w[^:]+:.+$")
s3 = boto3.client("s3")
threads_count = 56
terms_cache_header = (
    "struct<kind:string,id:string,term:string,label:string,type:string>"
)


def get_random_dataset(id, vcfLocations, vcfChromosomeMap, seed=0):
    random.seed(seed)

    item = Dataset(id=id)
    item.createDateTime = random.choice(
        [
            "1999-08-05T17:21:00+01:00",
            "2002-05-21T02:37:00-08:00",
            "2019-11-21T02:37:00-08:00",
            "2020-02-21T02:37:00-08:00",
            "2021-03-21T02:37:00-08:00",
            "2022-10-21T02:37:00-08:00",
        ]
    )
    item.dataUseConditions = random.choice(
        [
            {
                "duoDataUse": random.sample(
                    [
                        {
                            "id": "DUO:0000042",
                            "label": "general research use",
                            "version": "17-07-2016",
                        },
                        {
                            "id": "DUO:0000006",
                            "label": "health or medical or biomedical research",
                            "version": "17-07-2016",
                        },
                        {
                            "id": "DUO:0000007",
                            "label": "disease specific research",
                            "version": "17-07-2016",
                            "modifiers": random.sample(
                                [
                                    {
                                        "id": "MONDO:0043543",
                                        "label": "iatrogenic disease",
                                    },
                                    {
                                        "id": "MONDO:0043544",
                                        "label": "nosocomial infection",
                                    },
                                    {
                                        "id": "MONDO:0016778",
                                        "label": "iatrogenic botulism",
                                    },
                                    {
                                        "id": "EFO:0002613",
                                        "label": "iatrogenic Kaposi's sarcoma",
                                    },
                                    {
                                        "id": "MONDO:0034976",
                                        "label": "iatrogenic Creutzfeldt-Jakob disease",
                                    },
                                    {"id": "EFO:0010238", "label": "perinatal disease"},
                                ],
                                random.randint(0, 2),
                            ),
                        },
                        {
                            "id": "DUO:0000011",
                            "label": "population origins or ancestry research only",
                            "version": "17-07-2016",
                        },
                    ],
                    random.randint(0, 2),
                )
            },
            {
                "duoDataUse": [
                    {
                        "id": "DUO:0000004",
                        "label": "no restriction",
                        "version": "17-07-2016",
                    }
                ]
            },
        ]
    )
    item.description = random.choice(
        [
            "Simulation set 0.",
            "Simulation set 1.",
            "Simulation set 2.",
            "Simulation set 3.",
        ]
    )
    item.externalUrl = random.choice(
        [
            "http://example.org/wiki/Main_Page",
            "http://example.com/vcf/vcfs",
            "http://example.net/var/variants",
            "http://example.io/data/data",
        ]
    )
    item.info = {}
    item.name = random.choice(
        [
            "Dataset with synthetic data",
            "Dataset with simulated data",
            "Dataset with fake data",
        ]
    )
    item.updateDateTime = random.choice(
        ["2022-08-05T17:21:00+01:00", "2021-09-21T02:37:00-08:00"]
    )
    item.version = random.choice(
        [
            "v1.1",
            "v2.1",
            "v3.1",
        ]
    )

    dynamo_item = DynamoDataset(id)
    # keep 1 assemblyId for maximum stress on system
    dynamo_item.assemblyId = random.choice(["GRCH38"])
    dynamo_item.vcfGroups = [vcfLocations]
    dynamo_item.vcfLocations = vcfLocations
    dynamo_item.vcfChromosomeMap = vcfChromosomeMap

    item._assemblyId = dynamo_item.assemblyId
    item._vcfLocations = dynamo_item.vcfLocations
    item._vcfChromosomeMap = [
        item.attribute_values for item in dynamo_item.vcfChromosomeMap
    ]

    return item, dynamo_item


def get_random_cohort(id, size, seed=0):
    random.seed(seed)

    item = Cohort(id=id)
    item.cohortDataTypes = [
        random.choice(
            [
                {"id": "OGMS:0000015", "label": "clinical history"},
                {"id": "OBI:0000070", "label": "genotyping assay"},
                {"id": "OMIABIS:0000060", "label": "survey data"},
            ]
        )
        for _ in range(2)
    ]
    item.cohortDesign = {
        "id": random.choice(
            [
                "ga4gh:GA.01234abcde",
                "DUO:0000004",
                "orcid:0000-0003-3463-0775",
                "PMID:15254584",
            ]
        )
    }
    item.cohortSize = size
    item.cohortType = random.choice(["study-defined", "beacon-defined", "user-defined"])
    item.collectionEvents = {}
    item.exclusionCriteria = {}
    item.inclusionCriteria = {}
    item.name = random.choice(
        [
            "CGG group",
            "Gnihton genomics patients",
            "Gnihtemos patients",
            "Lamron cohort",
            "Gnizama Genomics",
            "ChetChet organisation for genomics",
        ]
    )

    return item


def get_random_individual(id, datasetId, cohortId, seed=0):
    random.seed(seed)

    item = Individual(id=id, datasetId=datasetId, cohortId=cohortId)
    item.diseases = random.sample(
        [
            # alzheimer
            {
                "diseaseCode": {
                    "id": "SNOMED:722600006",
                    "label": "Non-amnestic Alzheimer disease",
                }
            },
            {
                "diseaseCode": {
                    "id": "SNOMED:23853001",
                    "label": "Disorder of the central nervous system",
                }
            },
            {
                "diseaseCode": {
                    "id": "SNOMED:80690008",
                    "label": "Degenerative disease of the central nervous system",
                }
            },
            {"diseaseCode": {"id": "SNOMED:26929004", "label": "Alzheimer's disease"}},
            {
                "diseaseCode": {
                    "id": "SNOMED:135811000119107",
                    "label": "Lewy body dementia with behavioral disturbance (disorder)",
                }
            },
            {
                "diseaseCode": {
                    "id": "SNOMED:312991009",
                    "label": "Senile dementia of the Lewy body type (disorder)",
                }
            },
            #  neuroblastoma
            {
                "diseaseCode": {
                    "id": "SNOMED:281560004",
                    "label": "Neuroblastoma of brain",
                }
            },
            {
                "diseaseCode": {
                    "id": "SNOMED:734099007",
                    "label": "Neuroblastoma of central nervous system",
                }
            },
            {"diseaseCode": {"id": "SNOMED:254955001", "label": "Pituitary carcinoma"}},
            # malignant epithelial neoplasm
            {
                "diseaseCode": {
                    "id": "SNOMED:722688002",
                    "label": "Malignant epithelial neoplasm (disorder)",
                }
            },
            {
                "diseaseCode": {
                    "id": "SNOMED:399981008",
                    "label": "Neoplasm and/or hamartoma (disorder)",
                }
            },
            {
                "diseaseCode": {
                    "id": "SNOMED:369483006",
                    "label": "Malignant tumor involving vasa deferentia by direct extension from prostate (disorder)",
                }
            },
            # coronary heart disease
            {"diseaseCode": {"id": "SNOMED:194828000", "label": "Angina (disorder)"}},
            {
                "diseaseCode": {
                    "id": "SNOMED:429559004",
                    "label": "Typical angina (disorder)",
                }
            },
            {
                "diseaseCode": {
                    "id": "SNOMED:56265001",
                    "label": "Heart disease (disorder)",
                }
            },
            # diabetes
            {
                "diseaseCode": {
                    "id": "SNOMED:73211009",
                    "label": "Diabetes mellitus (disorder)",
                }
            },
            {
                "diseaseCode": {
                    "id": "SNOMED:81531005",
                    "label": "Diabetes mellitus type 2 in obese (disorder)",
                }
            },
            {
                "diseaseCode": {
                    "id": "SNOMED:359642000",
                    "label": "Diabetes mellitus type 2 in nonobese (disorder)",
                }
            },
        ],
        random.randint(0, 3),
    )
    item.ethnicity = random.choice(json.load(open("./data/individual-ethnicity.json")))
    item.exposures = random.sample(
        [
            {"exposureCode": {"id": "SNOMED:773760007", "label": "Traumatic event"}},
            {
                "exposureCode": {
                    "id": "SNOMED:242271001",
                    "label": "Accidental exposure to aerosol paint",
                }
            },
            {
                "exposureCode": {
                    "id": "SNOMED:242816007",
                    "label": "Exposure of patient to medical therapeutic radiation",
                }
            },
            {
                "exposureCode": {
                    "id": "SNOMED:242812009",
                    "label": "Exposure of patient to radiation from diagnostic isotopes",
                }
            },
            {
                "exposureCode": {
                    "id": "SNOMED:16090531000119106",
                    "label": "Exposure to arsenic",
                }
            },
            {
                "exposureCode": {
                    "id": "SNOMED:699373005",
                    "label": "Exposure to asbestos",
                }
            },
            {
                "exposureCode": {
                    "id": "SNOMED:409510007",
                    "label": "Inhalational exposure to biological agent",
                }
            },
        ],
        random.randint(0, 2),
    )
    item.geographicOrigin = random.choice(
        [
            {"id": "SNOMED:223498002", "label": "Africa"},
            {"id": "SNOMED:223544003", "label": "Angola"},
            {"id": "SNOMED:223356001", "label": "Anguilla island"},
            {"id": "SNOMED:223551007", "label": "Zimbabwe"},
            {"id": "SNOMED:223600005", "label": "India"},
            {"id": "SNOMED:223506007", "label": "Indian subcontinent"},
            {"id": "SNOMED:223713009", "label": "Argentina"},
            {"id": "SNOMED:223688001", "label": "United States of America"},
        ]
    )
    item.info = {}
    item.interventionsOrProcedures = random.sample(
        [
            {"procedureCode": {"id": "NCIT:C64264"}},
            {"procedureCode": {"id": "NCIT:C64263"}},
            {"procedureCode": {"id": "NCIT:C93025"}},
            {"procedureCode": {"id": "NCIT:C79426"}},
        ],
        random.randint(0, 2),
    )
    item.karyotypicSex = random.choice(
        [
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
            "OTHER_KARYOTYPE",
        ]
    )
    item.measures = []
    item.pedigrees = []
    item.phenotypicFeatures = []
    item.sex = random.choice(
        [
            {"id": "SNOMED:248152002", "label": "Female"},
            {"id": "SNOMED:407377005", "label": "Female-to-male transsexual"},
            {"id": "SNOMED:248153007", "label": "Male"},
            {
                "id": "SNOMED:407378000",
                "label": "Surgically transgendered transsexual, male-to-female",
            },
            {"id": "SNOMED:407374003", "label": "Transsexual"},
        ]
    )
    item.treatments = []

    return item


def get_random_biosample(id, datasetId, cohortId, individualId, seed=0):
    random.seed(seed)

    item = Biosample(
        id=id, datasetId=datasetId, cohortId=cohortId, individualId=individualId
    )
    item.biosampleStatus = random.choice(
        [
            {"id": "SNOMED:365641003", "label": "Minor blood groups - finding"},
            {"id": "SNOMED:276447000", "label": "Mite present"},
            {
                "id": "SNOMED:702781009",
                "label": "Mitochondrial 1555 A to G mutation negative",
            },
            {
                "id": "SNOMED:702782002",
                "label": "Mitochondrial 1555 A to G mutation positive",
            },
            {"id": "SNOMED:310293008", "label": "Mitochondrial antibodies negative"},
            {"id": "SNOMED:310294002", "label": "Mitochondrial antibodies positive"},
        ]
    )
    item.collectionDate = random.choice(
        ["2021-04-23", "2022-04-23", "2019-04-23", "2018-04-23", "2015-04-23"]
    )
    item.collectionMoment = random.choice(["P32Y6M1D", "P7D"])
    item.diagnosticMarkers = []
    item.histologicalDiagnosis = random.choice(
        [
            {},
            {"id": "SNOMED:237592006", "label": "Abnormality of bombesin secretion"},
            {"id": "SNOMED:362965005", "label": "Disorder of body system (disorder)"},
            {"id": "SNOMED:719046005", "label": "12q14 microdeletion syndrome"},
            {"id": "SNOMED:771439009", "label": "14q22q23 microdeletion syndrome"},
        ]
    )
    item.measurements = []
    item.obtentionProcedure = random.choice(
        [
            {},
            {"procedureCode": {"id": "NCIT:C15189", "label": "biopsy"}},
            {
                "procedureCode": {
                    "id": "NCIT:C157179",
                    "label": "FGFR1 Mutation Analysis",
                }
            },
        ]
    )
    item.pathologicalStage = random.choice(
        [{}, {}, {"id": "NCIT:C27977", "label": "Stage IIIA"}]
    )
    item.pathologicalTnmFinding = [
        random.choice(
            [
                {},
                {"id": "NCIT:C48725", "label": "T2a Stage Finding"},
                {"id": "NCIT:C48709", "label": "N1c Stage Finding"},
                {"id": "NCIT:C48699", "label": "M0 Stage Finding"},
            ]
        )
    ]
    item.phenotypicFeatures = []
    item.sampleOriginDetail = random.choice(
        [
            {},
            {"id": "SNOMED:258500001", "label": "Nasopharyngeal swab"},
            {"id": "SNOMED:472881004", "label": "Pharyngeal swab"},
            {"id": "SNOMED:258603007", "label": "Respiratory specimen"},
            {"id": "SNOMED:258497007", "label": "Abscess swab"},
            {"id": "SNOMED:258407001", "label": "Abscess tissue"},
            {
                "id": "SNOMED:385338007",
                "label": "Specimen from anus obtained by transanal disk excision",
            },
            {"id": "SNOMED:734336008", "label": "Specimen from aorta"},
        ]
    )
    item.sampleOriginType = random.choice(
        [
            {"id": "SNOMED:31675002", "label": "Capillary blood"},
            {"id": "SNOMED:782814004", "label": "Cultured autograft of skin"},
            {"id": "SNOMED:702451000", "label": "Cultured cells"},
            {"id": "SNOMED:421955000", "label": "Culture medium"},
            {"id": "SNOMED:422236008", "label": "Agar medium"},
        ]
    )
    item.sampleProcessing = random.choice(
        [
            {},
            {
                "id": "SNOMED:87021001",
                "label": "Mechanical vitrectomy by pars plana approach",
            },
            {
                "id": "SNOMED:72019009",
                "label": "Mechanical vitrectomy by posterior approach",
            },
            {"id": "SNOMED:18809007", "label": "Meckel's ganglionectomy"},
        ]
    )
    item.sampleStorage = ({},)
    item.tumorGrade = random.choice([{}, {"id": "NCIT:C28080", "label": "Grade 3a"}])
    item.tumorProgression = random.choice(
        [
            {},
            {"id": "NCIT:C84509", "label": "Primary Malignant Neoplasm"},
            {"id": "NCIT:C4813", "label": "Recurrent Malignant Neoplasm"},
        ]
    )
    item.info = {}
    item.notes = ""

    return item


def get_random_run(id, datasetId, cohortId, individualId, biosampleId, seed=0):
    random.seed(seed)

    item = Run(
        id=id,
        datasetId=datasetId,
        cohortId=cohortId,
        individualId=individualId,
        biosampleId=biosampleId,
    )
    item.libraryLayout = "PAIRED"
    item.librarySelection = "RANDOM"
    item.librarySource = random.choice(
        [
            {"id": "GENEPIO:0001969", "label": "other library source"},
            {"id": "GENEPIO:0001966", "label": "genomic source"},
        ]
    )
    item.libraryStrategy = "WGS"
    idx = random.choice([0, 1, 2])
    item.platform = ["Illumina", "PacBio", "NanoPore"][idx]
    item.platformModel = [
        {"id": "OBI:0002048", "label": "Illumina HiSeq 3000"},
        {"id": "OBI:0002012", "label": "PacBio RS II"},
        {"id": "OBI:0002750", "label": "Oxford Nanopore MinION"},
    ][idx]
    item.runDate = random.choice(["2021-10-18", "2022-08-08", "2018-01-01"])

    return item


def get_random_analysis(
    id, datasetId, cohortId, individualId, biosampleId, runId, vcfSampleId, seed=0
):
    random.seed(seed)

    item = Analysis(
        id=id,
        datasetId=datasetId,
        cohortId=cohortId,
        individualId=individualId,
        biosampleId=biosampleId,
        vcfSampleId=vcfSampleId,
        runId=runId,
    )
    item.aligner = random.choice(["bwa-0.7.8", "minimap2", "bowtie"])
    item.analysisDate = (
        f"{random.randint(2018, 2022)}-{random.randint(1, 12)}-{random.randint(1, 28)}"
    )
    item.pipelineName = f"pipeline {random.randint(1, 5)}"
    item.pipelineRef = "Example"
    item.variantCaller = random.choice(["GATK4.0", "SoapSNP", "kmer2snp"])

    return item


def clean_files(bucket, prefix):
    has_more = True
    pbar = tqdm(desc="Cleaning Files")
    while has_more:
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        files_to_delete = []
        for object in response.get("Contents", []):
            files_to_delete.append({"Key": object["Key"]})
        if files_to_delete:
            s3.delete_objects(Bucket=bucket, Delete={"Objects": files_to_delete})
        pbar.update(len(files_to_delete))
        has_more = response["IsTruncated"]


def clean():
    with DynamoDataset.batch_write() as batch:
        for dynamo_item in tqdm(DynamoDataset.scan(), desc="Cleaning Dataset"):
            batch.delete(dynamo_item)

    with Ontology.batch_write() as batch:
        for dynamo_item in tqdm(Ontology.scan(), desc="Cleaning Ontology"):
            batch.delete(dynamo_item)

    with Anscestors.batch_write() as batch:
        for dynamo_item in tqdm(Anscestors.scan(), desc="Cleaning Anscestors"):
            batch.delete(dynamo_item)

    with Descendants.batch_write() as batch:
        for dynamo_item in tqdm(Descendants.scan(), desc="Cleaning Descendants"):
            batch.delete(dynamo_item)

    with VariantQuery.batch_write() as batch:
        for dynamo_item in tqdm(VariantQuery.scan(), desc="Cleaning VariantQuery"):
            batch.delete(dynamo_item)

    with VariantResponse.batch_write() as batch:
        for dynamo_item in tqdm(
            VariantResponse.scan(), desc="Cleaning VariantResponse"
        ):
            batch.delete(dynamo_item)

    clean_files(ATHENA_METADATA_BUCKET, "")


def extract_terms(array):
    for item in array:
        if type(item) == dict:
            label = item.get("label", "")
            typ = item.get("type", "string")
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


def simulate_datasets_cohorts(template):
    dynamo_items = []
    dataset_samples = dict()
    path_datasets = f"{datasets_path}.orc"
    path_datasets_dynamo = f"{datasets_path}.json"
    path_datasets_terms = f"{datasets_path}-terms.orc"
    path_cohorts = f"{cohorts_path}.orc"
    path_cohorts_terms = f"{cohorts_path}-terms.orc"

    # datasets
    terms_file = open(path_datasets_terms, "wb+")
    terms_writer = pyorc.Writer(terms_file, terms_cache_header)
    file, writer = get_writer(Dataset, path_datasets)
    n = 1

    for line in open(template).read().strip().split("\n"):
        if line[0] == "#":
            continue
        n += 1
        data = line.strip().split(" ")
        multiplier = int(data[0])
        vcfs = data[1:]
        vcfChromosomeMap = []

        samples = get_samples(vcfs[0])

        # vcf chromosomes
        for vcf in set(vcfs):
            errored, _, chroms = get_vcf_chromosomes(vcf)
            assert errored == False, "Unable to fetch chromosomes"
            vcfm = VcfChromosomeMap()
            vcfm.vcf = vcf
            vcfm.chromosomes = chroms
            vcfChromosomeMap.append(vcfm)

        for m in tqdm(range(multiplier), desc="Simulating datasets"):
            id = f"{n}-{m}"
            dataset, dynamo_item = get_random_dataset(
                id, vcfs, vcfChromosomeMap, seed=id
            )

            for term, label, typ in extract_terms([jsons.dump(dataset)]):
                terms_writer.write(("datasets", dataset.id, term, label, typ))

            dynamo_item.sampleCount = len(samples)
            # dynamo_item.sampleNames = samples
            dynamo_item.sampleNames = ["None"]
            dataset_samples[id] = samples
            dynamo_items.append(dynamo_item)
            write_local(Dataset, dataset, writer)
    writer.close()
    file.close()
    terms_writer.close()
    terms_file.close()

    with open(path_datasets_dynamo, "w+") as jsonf:
        for item in dynamo_items:
            jsonf.write(item.to_json() + "\n")

    # cohorts
    terms_file = open(path_cohorts_terms, "wb+")
    terms_writer = pyorc.Writer(terms_file, terms_cache_header)
    file, writer = get_writer(Cohort, path_cohorts)

    for dataset in tqdm(dynamo_items, desc="Simulating cohorts"):
        id = dataset.id
        cohort = get_random_cohort(id=id, size=dataset.sampleCount, seed=id)

        for term, label, typ in extract_terms([jsons.dump(cohort)]):
            terms_writer.write(("cohorts", cohort.id, term, label, typ))

        write_local(Cohort, cohort, writer)

    writer.close()
    file.close()
    terms_writer.close()
    terms_file.close()

    return dynamo_items, dataset_samples


def simulate_individuals(dynamo_items):
    def runner(thread_id):
        idx = 1
        thread_path = f"./{individuals_path}-{thread_id}-{idx}.orc"
        thread_terms_path = f"./{individuals_path}-terms-{thread_id}.orc"
        terms_file = open(thread_terms_path, "wb+")
        terms_writer = pyorc.Writer(terms_file, terms_cache_header)
        file, writer = get_writer(Individual, thread_path)
        pbar = tqdm(desc=f"Individuals thread - {thread_id}", position=thread_id)

        for n, dataset in enumerate(dynamo_items):
            if n % threads_count != thread_id:
                continue

            id = dataset.id
            nosamples = dataset.sampleCount

            for itr in range(nosamples):
                individual = get_random_individual(
                    id=f"{id}-{itr}", datasetId=id, cohortId=id, seed=f"{id}-{itr}"
                )

                for term, label, typ in extract_terms([jsons.dump(individual)]):
                    terms_writer.write(("individuals", individual.id, term, label, typ))

                write_local(Individual, individual, writer)
                idx += 1

                if idx % 1000000 == 0:
                    writer.close()
                    file.close()
                    thread_path = f"./{individuals_path}-{thread_id}-{idx}.orc"
                    file, writer = get_writer(Individual, thread_path)
                pbar.update()

        writer.close()
        file.close()
        terms_writer.close()
        terms_file.close()
        pbar.close()

    threads = [
        multiprocessing.Process(target=runner, args=(thread_id,))
        for thread_id in range(threads_count)
    ]
    [thread.start() for thread in threads]
    [thread.join() for thread in threads]
    print()


def simulate_biosamples(dynamo_items):
    def runner(thread_id):
        idx = 1
        thread_path = f"./{biosamples_path}-{thread_id}-{idx}.orc"
        thread_terms_path = f"./{biosamples_path}-terms-{thread_id}.orc"
        terms_file = open(thread_terms_path, "wb+")
        terms_writer = pyorc.Writer(terms_file, terms_cache_header)
        file, writer = get_writer(Biosample, thread_path)
        pbar = tqdm(desc=f"Biosamples thread - {thread_id}", position=thread_id)

        for n, dataset in enumerate(dynamo_items):
            if n % threads_count != thread_id:
                continue

            id = dataset.id
            nosamples = dataset.sampleCount

            for itr in range(nosamples):
                biosample = get_random_biosample(
                    id=f"{id}-{itr}",
                    datasetId=id,
                    cohortId=id,
                    individualId=f"{id}-{itr}",
                    seed=f"{id}-{itr}",
                )

                for term, label, typ in extract_terms([jsons.dump(biosample)]):
                    terms_writer.write(("biosamples", biosample.id, term, label, typ))

                write_local(Biosample, biosample, writer)
                idx += 1

                if idx % 1000000 == 0:
                    writer.close()
                    file.close()
                    thread_path = f"./{biosamples_path}-{thread_id}-{idx}.orc"
                    file, writer = get_writer(Biosample, thread_path)

                pbar.update()

        writer.close()
        file.close()
        terms_writer.close()
        terms_file.close()
        pbar.close()

    threads = [
        multiprocessing.Process(target=runner, args=(thread_id,))
        for thread_id in range(threads_count)
    ]
    [thread.start() for thread in threads]
    [thread.join() for thread in threads]
    print()


def simulate_runs(dynamo_items):
    def runner(thread_id):
        idx = 1
        thread_path = f"./{runs_path}-{thread_id}-{idx}.orc"
        thread_terms_path = f"./{runs_path}-terms-{thread_id}.orc"
        terms_file = open(thread_terms_path, "wb+")
        terms_writer = pyorc.Writer(terms_file, terms_cache_header)
        file, writer = get_writer(Run, thread_path)
        pbar = tqdm(desc=f"Runs thread - {thread_id}", position=thread_id)

        for n, dataset in enumerate(dynamo_items):
            if n % threads_count != thread_id:
                continue

            id = dataset.id
            nosamples = dataset.sampleCount

            for itr in range(nosamples):
                run = get_random_run(
                    id=f"{id}-{itr}",
                    datasetId=id,
                    cohortId=id,
                    individualId=f"{id}-{itr}",
                    biosampleId=f"{id}-{itr}",
                    seed=f"{id}-{itr}",
                )

                for term, label, typ in extract_terms([jsons.dump(run)]):
                    terms_writer.write(("runs", run.id, term, label, typ))

                write_local(Run, run, writer)
                idx += 1

                if idx % 1000000 == 0:
                    writer.close()
                    file.close()
                    thread_path = f"./{runs_path}-{thread_id}-{idx}.orc"
                    file, writer = get_writer(Run, thread_path)

                pbar.update()

        writer.close()
        file.close()
        terms_writer.close()
        terms_file.close()
        pbar.close()

    threads = [
        multiprocessing.Process(target=runner, args=(thread_id,))
        for thread_id in range(threads_count)
    ]
    [thread.start() for thread in threads]
    [thread.join() for thread in threads]
    print()


def simulate_analyses(dynamo_items, dataset_samples):
    def runner(thread_id):
        idx = 1
        thread_path = f"./{analyses_path}-{thread_id}-{idx}.orc"
        thread_terms_path = f"./{analyses_path}-terms-{thread_id}.orc"
        terms_file = open(thread_terms_path, "wb+")
        terms_writer = pyorc.Writer(terms_file, terms_cache_header)
        file, writer = get_writer(Analysis, thread_path)
        pbar = tqdm(desc=f"Analyses thread - {thread_id}", position=thread_id)

        for n, dataset in enumerate(dynamo_items):
            if n % threads_count != thread_id:
                continue

            id = dataset.id
            nosamples = dataset.sampleCount

            for itr in range(nosamples):
                analysis = get_random_analysis(
                    id=f"{id}-{itr}",
                    datasetId=id,
                    cohortId=id,
                    individualId=f"{id}-{itr}",
                    biosampleId=f"{id}-{itr}",
                    runId=f"{id}-{itr}",
                    # vcfSampleId=dataset.sampleNames[itr],
                    vcfSampleId=dataset_samples[id][itr],
                    seed=f"{id}-{itr}",
                )

                for term, label, typ in extract_terms([jsons.dump(analysis)]):
                    terms_writer.write(("analyses", analysis.id, term, label, typ))

                write_local(Analysis, analysis, writer)
                idx += 1
                if idx % 1000000 == 0:
                    writer.close()
                    file.close()
                    thread_path = f"./{analyses_path}-{thread_id}-{idx}.orc"
                    file, writer = get_writer(Analysis, thread_path)

                pbar.update()

        writer.close()
        file.close()
        terms_writer.close()
        terms_file.close()
        pbar.close()

    threads = [
        multiprocessing.Process(target=runner, args=(thread_id,))
        for thread_id in range(threads_count)
    ]
    [thread.start() for thread in threads]
    [thread.join() for thread in threads]
    print()


def simulate(template):
    dynamo_items, dataset_samples = simulate_datasets_cohorts(template)
    print("Simulating individuals", flush=True)
    simulate_individuals(dynamo_items)
    print("Simulating biosamples", flush=True)
    simulate_biosamples(dynamo_items)
    print("Simulating runs", flush=True)
    simulate_runs(dynamo_items)
    print("Simulating analyses", flush=True)
    simulate_analyses(dynamo_items, dataset_samples)
    print(flush=True, end="")


def upload():
    pool = concurrent.futures.ProcessPoolExecutor(max_workers=threads_count)

    # upload datasets
    pool.submit(
        upload_local,
        f"{datasets_path}.orc",
        f"s3://{ATHENA_METADATA_BUCKET}/datasets-cache/combined-datasets.orc",
    )
    pool.submit(
        upload_local,
        f"{datasets_path}-terms.orc",
        f"s3://{ATHENA_METADATA_BUCKET}/terms-cache/datasets.orc",
    )

    # upload cohorts
    pool.submit(
        upload_local,
        f"{cohorts_path}.orc",
        f"s3://{ATHENA_METADATA_BUCKET}/cohorts-cache/combined-cohorts.orc",
    )
    pool.submit(
        upload_local,
        f"{cohorts_path}-terms.orc",
        f"s3://{ATHENA_METADATA_BUCKET}/terms-cache/cohorts.orc",
    )

    # upload individuals
    for thread in range(threads_count):
        pool.submit(
            upload_local,
            f"{individuals_path}-terms-{thread}.orc",
            f"s3://{ATHENA_METADATA_BUCKET}/terms-cache/individuals-{thread}.orc",
        )
        pool.submit(
            upload_local,
            f"{biosamples_path}-terms-{thread}.orc",
            f"s3://{ATHENA_METADATA_BUCKET}/terms-cache/biosamples-{thread}.orc",
        )
        pool.submit(
            upload_local,
            f"{runs_path}-terms-{thread}.orc",
            f"s3://{ATHENA_METADATA_BUCKET}/terms-cache/runs-{thread}.orc",
        )
        pool.submit(
            upload_local,
            f"{analyses_path}-terms-{thread}.orc",
            f"s3://{ATHENA_METADATA_BUCKET}/terms-cache/analyses-{thread}.orc",
        )

        for file in glob(f"{individuals_path}-{thread}-*"):
            idx = file.split("/")[-1].replace(".orc", "")
            pool.submit(
                upload_local,
                file,
                f"s3://{ATHENA_METADATA_BUCKET}/individuals-cache/individuals-{thread}-{idx}.orc",
            )

        for file in glob(f"{biosamples_path}-{thread}-*"):
            idx = file.split("/")[-1].replace(".orc", "")
            pool.submit(
                upload_local,
                file,
                f"s3://{ATHENA_METADATA_BUCKET}/biosamples-cache/biosamples-{thread}-{idx}",
            )

        for file in glob(f"{runs_path}-{thread}-*"):
            idx = file.split("/")[-1].replace(".orc", "")
            pool.submit(
                upload_local,
                file,
                f"s3://{ATHENA_METADATA_BUCKET}/runs-cache/runs-{thread}-{idx}",
            )

        for file in glob(f"{analyses_path}-{thread}-*"):
            idx = file.split("/")[-1].replace(".orc", "")
            pool.submit(
                upload_local,
                file,
                f"s3://{ATHENA_METADATA_BUCKET}/analyses-cache/analyses-{thread}-{idx}",
            )
    pool.shutdown()

    with DynamoDataset.batch_write() as batch:
        for line in tqdm(
            open(f"{datasets_path}.json"), desc="Writing datasets to DynamoDB"
        ):
            item = DynamoDataset()
            item.from_json(line.strip())
            batch.save(item)


if __name__ == "__main__":
    if sys.argv[1] not in ("simulate", "upload", "clean"):
        print("Usage: \n\t$ python simulate.py [simulate|upload|clean]\n")
        sys.exit(1)

    if sys.argv[1] == "simulate":
        if len(sys.argv) != 4:
            print(
                f"A prefix must be stated\n\tUsage: $ python simulate.py {sys.argv[1]} DIR_NAME TEMPLATE"
            )
            sys.exit(1)

        prefix = sys.argv[2]
        template = sys.argv[3]
        datasets_path = f"{prefix}/simulated-datasets"
        cohorts_path = f"{prefix}/simulated-cohorts"
        individuals_path = f"{prefix}/simulated-individuals"
        biosamples_path = f"{prefix}/simulated-biosamples"
        runs_path = f"{prefix}/simulated-runs"
        analyses_path = f"{prefix}/simulated-analyses"

        if not (prefix.startswith(".") or prefix.startswith("/")):
            shutil.rmtree(prefix, ignore_errors=True)

        os.mkdir(prefix)
        simulate(template)

    elif sys.argv[1] == "upload":
        if len(sys.argv) != 3:
            print(
                f"A prefix must be stated\n\tUsage: $ python simulate.py {sys.argv[1]} DIR_NAME"
            )
            sys.exit(1)

        prefix = sys.argv[2]
        datasets_path = f"{prefix}/simulated-datasets"
        cohorts_path = f"{prefix}/simulated-cohorts"
        individuals_path = f"{prefix}/simulated-individuals"
        biosamples_path = f"{prefix}/simulated-biosamples"
        runs_path = f"{prefix}/simulated-runs"
        analyses_path = f"{prefix}/simulated-analyses"

        upload()
    else:
        clean()
