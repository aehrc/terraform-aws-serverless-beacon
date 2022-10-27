import os

import boto3
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, UnicodeSetAttribute


DYNAMO_ONTOLOGIES_TABLE = os.environ['DYNAMO_ONTOLOGIES_TABLE']
DYNAMO_DESCENDANTS_TABLE = os.environ['DYNAMO_DESCENDANTS_TABLE']
DYNAMO_ANSCESTORS_TABLE = os.environ['DYNAMO_ANSCESTORS_TABLE']
SESSION = boto3.session.Session()
REGION = SESSION.region_name


# Ontologies table
class Ontology(Model):
    class Meta:
        table_name = DYNAMO_ONTOLOGIES_TABLE
        region = REGION

    prefix = UnicodeAttribute(hash_key=True)
    data = UnicodeAttribute()


# Descendants table
class Descendants(Model):
    class Meta:
        table_name = DYNAMO_DESCENDANTS_TABLE
        region = REGION

    term = UnicodeAttribute(hash_key=True)
    descendants = UnicodeSetAttribute()


# Anscestors table
class Anscestors(Model):
    class Meta:
        table_name = DYNAMO_ANSCESTORS_TABLE
        region = REGION

    term = UnicodeAttribute(hash_key=True)
    anscestors = UnicodeSetAttribute()


# TODO further partition these terms under different entity kinds
def expand_terms(filters):
    terms = set()
    for filter in filters:
        term = filter.get('id')
        if filter.get('includeDescendantTerms', True):
            try:
                item = Descendants.get(term)
                terms.update(item.descendants)
            except Descendants.DoesNotExist:
                terms.add(term)
        else:
            terms.add(term)
    return ','.join([f"'{term}'" for term in terms])


if __name__ == '__main__':
    pass
