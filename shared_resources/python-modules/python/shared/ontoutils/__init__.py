import json
import time
import urllib
from functools import lru_cache

import requests

from shared.dynamodb import Ontology, Descendants, Anscestors


ENSEMBL_OLS_V4 = "https://www.ebi.ac.uk/ols4/api/ontologies"
ONTOSERVER = "https://r4.ontoserver.csiro.au/fhir/ValueSet/$expand"


@lru_cache()
def get_term_ancestors_in_beacon(term):
    terms = set()
    try:
        terms.update(Anscestors.get(term).anscestors)
    except Anscestors.DoesNotExist:
        terms.add(term)
    return terms


@lru_cache()
def get_term_descendants_in_beacon(term: str):
    terms = set()
    try:
        terms.update(Descendants.get(term).descendants)
    except Descendants.DoesNotExist:
        terms.add(term)
    return terms


@lru_cache()
def get_term_all_ancestors(term: str):
    term, ancestors = request_hierarchy(term, True)
    ancestors.add(term)

    return ancestors


@lru_cache()
def get_term_all_descendants(term: str):
    term, descendants = request_hierarchy(term, False)
    descendants.add(term)

    return descendants


@lru_cache()
def get_ontology_details(ontology) -> Ontology:
    details = None
    try:
        details = Ontology.get(ontology.lower())
    except Ontology.DoesNotExist:
        if ontology == "SNOMED":
            # use ontoserver details
            details = Ontology(ontology.lower())
            details = Ontology("snomed")
            details.name = "SNOMED Clinical Terms Australian extension"
            details.url = "http://snomed.info/sct"
            details.version = (
                "http://snomed.info/sct/32506021000036107/version/20210204"
            )
            details.namespacePrefix = "http://snomed.info/sct"
            details.iriPrefix = "http://snomed.info/sct"
            details.save()
        else:
            # use ENSEMBL
            if response := requests.get(f"{ENSEMBL_OLS_V4}/{ontology}"):
                response_json = response.json()

                try:
                    details = Ontology(response_json["ontologyId"].lower())
                    details.name = response_json["config"]["title"]
                    details.url = response_json["config"]["versionIri"]
                    details.version = response_json["version"]
                    details.namespacePrefix = response_json["config"]["preferredPrefix"]
                    details.iriPrefix = ""
                    details.save()
                except:
                    return None

    return details


@lru_cache()
def request_ontoserver_hierarchy(term: str, fetch_ancestors=True):
    snomed = "SNOMED" in term.upper()
    retries = 1
    response = None
    details = get_ontology_details("SNOMED")

    while (not response or response.status_code != 200) and retries < 10:
        retries += 1
        response = requests.post(
            ONTOSERVER,
            json={
                "resourceType": "Parameters",
                "parameter": [
                    {
                        "name": "valueSet",
                        "resource": {
                            "resourceType": "ValueSet",
                            "compose": {
                                "include": [
                                    {
                                        "system": details.url,
                                        "filter": [
                                            {
                                                "property": "concept",
                                                "op": (
                                                    "generalizes"
                                                    if fetch_ancestors
                                                    else "descendent-of"
                                                ),
                                                "value": f"{term.replace('SNOMED:', '')}",
                                            }
                                        ],
                                    }
                                ]
                            },
                        },
                    }
                ],
            },
        )
        if response.status_code == 200:
            response_json = response.json()
            member_labels = dict()
            for response_term in response_json["expansion"]["contains"]:
                member_labels[
                    (
                        "SNOMED:" + response_term["code"]
                        if snomed
                        else response_term["code"]
                    )
                ] = response_term["display"]
            return (term, member_labels)
        else:
            time.sleep(1)

    raise Exception(f"Error fetching term from Ontoserver {term}")


@lru_cache()
def request_ensembl_term_details(ontology: str, code: str):
    url = f"{ENSEMBL_OLS_V4}/{ontology}/terms"
    if response := requests.get(
        url,
        {
            "short_form": f"{ontology}_{code}".upper(),
        },
    ):
        response_json = response.json()
        return response_json
    return None


@lru_cache()
def request_ensembl_hierarchy(term: str, fetch_ancestors=True):
    ontology, code = term.split(":")
    ontology_details = get_ontology_details(ontology)
    # if no details available, it is probably not an ontology term
    if not ontology_details:
        return (term, dict())

    term_details = request_ensembl_term_details(ontology, code)

    # not available in esembl OLS
    if not term_details or len(term_details["_embedded"]["terms"]) == 0:
        return (term, dict())

    try:
        if fetch_ancestors:
            url = term_details["_embedded"]["terms"][0]["_links"][
                "hierarchicalAncestors"
            ]["href"]
        else:
            url = term_details["_embedded"]["terms"][0]["_links"][
                "hierarchicalDescendants"
            ]["href"]
    except:
        return (term, dict())

    if response := requests.get(url, {"size": 100}):
        response_json = response.json()
        member_labels = dict()
        for response_term in response_json["_embedded"]["terms"]:
            obo_id = response_term["obo_id"]
            label = response_term["label"]
            if obo_id:
                member_labels[obo_id] = label
        return (term, member_labels)

    raise Exception(f"Error fetching term from Ensembl OLS {term}")


@lru_cache()
def request_hierarchy(term, fetch_ancestors=True):
    if term.startswith("SNOMED"):
        return request_ontoserver_hierarchy(term, fetch_ancestors)
    return request_ensembl_hierarchy(term, fetch_ancestors)
