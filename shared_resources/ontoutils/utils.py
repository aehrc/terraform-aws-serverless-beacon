import queue

import requests


def get_child_terms(sno_med_parent_terms=[]):
    responses = queue.Queue()

    def download(term, ontologies_in_beacon, queue):
        ontologies_url = f"https://r4.ontoserver.csiro.au/fhir/CodeSystem/$lookup?system=http://snomed.info/sct&code={term}&property=child"
        response = requests.get(ontologies_url)

        if response:
            response_json = response.json()
            chosen_resources = []
            for ontology in response_json["_embedded"]["ontologies"]:
                res_id = ontology["ontologyId"]

                if res_id.upper() not in ontologies_in_beacon:
                    continue

                resource = {
                    "id": res_id,
                    "name": ontology["config"]["title"],
                    "url": ontology["config"]["fileLocation"],
                    "version": ontology["config"]["version"],
                    "namespacePrefix": ontology["config"]["preferredPrefix"],
                    "iriPrefix": ontology["config"]["baseUris"][0],
                }

                chosen_resources.append()
        else:
            raise Exception("API Error")
