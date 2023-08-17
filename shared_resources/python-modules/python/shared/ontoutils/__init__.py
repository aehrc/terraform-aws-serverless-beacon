import json
import time
import urllib
from functools import lru_cache

import requests

from shared.dynamodb import Ontology, Descendants, Anscestors


ENSEMBL_OLS = "https://www.ebi.ac.uk/ols/api/ontologies"
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
            if response := requests.get(f"{ENSEMBL_OLS}/{ontology}"):
                response_json = response.json()
                details = Ontology(response_json["ontologyId"].lower())
                details.name = response_json["config"]["title"]
                details.url = response_json["config"]["id"]
                details.version = response_json["config"]["version"]
                details.namespacePrefix = response_json["config"]["preferredPrefix"]
                details.iriPrefix = response_json["config"]["baseUris"][0]
                details.save()

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
                                                "op": "generalizes"
                                                if fetch_ancestors
                                                else "descendent-of",
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
            members = set()
            for response_term in response_json["expansion"]["contains"]:
                members.add(
                    "SNOMED:" + response_term["code"]
                    if snomed
                    else response_term["code"]
                )
            return (term, members)
        else:
            time.sleep(1)

    raise Exception(f"Error fetching term from Ontoserver {term}")


@lru_cache()
def request_ensembl_hierarchy(term: str, fetch_ancestors=True):
    ontology, code = term.split(":")
    details = get_ontology_details(ontology)
    # if no details available, it is probably not an ontology term
    if not details:
        return (term, set())

    iri = details.iriPrefix + code
    iri_double_encoded = urllib.parse.quote_plus(urllib.parse.quote_plus(iri))
    url = f"{ENSEMBL_OLS}/{ontology}/terms/{iri_double_encoded}/{'hierarchicalAncestors' if fetch_ancestors else 'hierarchicalDescendants'}"

    if response := requests.get(url):
        response_json = response.json()
        members = set()
        for response_term in response_json["_embedded"]["terms"]:
            obo_id = response_term["obo_id"]
            if obo_id:
                members.add(obo_id)
        return (term, members)

    raise Exception(f"Error fetching term from Ensembl OLS {term}")


@lru_cache()
def request_hierarchy(term, fetch_ancestors=True):
    if term.startswith("SNOMED"):
        return request_ontoserver_hierarchy(term, fetch_ancestors)
    return request_ensembl_hierarchy(term, fetch_ancestors)
