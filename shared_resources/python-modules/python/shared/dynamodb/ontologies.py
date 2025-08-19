import boto3
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, UnicodeSetAttribute

from shared.utils import ENV_DYNAMO


SESSION = boto3.session.Session()
REGION = SESSION.region_name


# Ontologies table
class Ontology(Model):
    class Meta:
        table_name = ENV_DYNAMO.DYNAMO_ONTOLOGIES_TABLE
        region = REGION

    id = UnicodeAttribute(hash_key=True)
    name = UnicodeAttribute(default_for_new=None, null=True)
    url = UnicodeAttribute()
    version = UnicodeAttribute(default_for_new=None, null=True)
    namespacePrefix = UnicodeAttribute()
    iriPrefix = UnicodeAttribute()


# Descendants table
class Descendants(Model):
    class Meta:
        table_name = ENV_DYNAMO.DYNAMO_DESCENDANTS_TABLE
        region = REGION

    term = UnicodeAttribute(hash_key=True)
    descendants = UnicodeSetAttribute()


# Anscestors table
class Anscestors(Model):
    class Meta:
        table_name = ENV_DYNAMO.DYNAMO_ANSCESTORS_TABLE
        region = REGION

    term = UnicodeAttribute(hash_key=True)
    anscestors = UnicodeSetAttribute()

# Term details table
class TermLabels(Model):
    class Meta:
        table_name = ENV_DYNAMO.DYNAMO_TERM_LABELS_TABLE
        region = REGION

    term = UnicodeAttribute(hash_key=True)
    label = UnicodeAttribute()


if __name__ == "__main__":
    pass
