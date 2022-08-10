import jsons
from collections import defaultdict
from typing import Any, List, Dict
import random
import boto3
from uuid import uuid4
import json


s3 = boto3.client('s3')


class OntologyTerm(jsons.JsonSerializable):
    id: str
    label: str


class Individual(jsons.JsonSerializable):
    def __init__(
                self,
                *,
                id="",
                datasetIds=[],
                diseases=[],
                ethnicity={},
                exposures=[],
                geographicOrigin={},
                info={},
                interventionsOrProcedures=[],
                karyotypicSex="",
                measures=[],
                pedigrees=[],
                phenotypicFeatures=[],
                sex={},
                treatments=[]
            ):
        self.id = id
        self.datasetIds = datasetIds
        self.diseases = diseases
        self.ethnicity = ethnicity
        self.exposures = exposures
        self.geographicOrigin = geographicOrigin
        self.info = info
        self.interventionsOrProcedures = interventionsOrProcedures
        self.karyotypicSex = karyotypicSex
        self.measures = measures
        self.pedigrees = pedigrees
        self.phenotypicFeatures = phenotypicFeatures
        self.sex = sex
        self.treatments = treatments

