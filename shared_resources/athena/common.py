import jsons
import boto3


class OntologyTerm(jsons.JsonSerializable):
    id: str
    label: str
