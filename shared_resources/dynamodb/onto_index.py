import os

from pynamodb.models import Model
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from pynamodb.attributes import UnicodeAttribute


ONTO_INDEX_TABLE = os.environ['ONTO_INDEX_TABLE']


# Terms index
class TermIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = 'term_index'
        projection = AllProjection()
        billing_mode = "PAY_PER_REQUEST"

    term = UnicodeAttribute(hash_key=True)


# TableNames
class TableIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = 'table_index'
        projection = AllProjection()
        billing_mode = "PAY_PER_REQUEST"

    tableName = UnicodeAttribute(hash_key=True)


# TableNames
class TableTermsIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = 'tableterms_index'
        projection = AllProjection()
        billing_mode = "PAY_PER_REQUEST"

    tableTerms = UnicodeAttribute(hash_key=True)


# datasets table
class OntoData(Model):
    class Meta:
        table_name = ONTO_INDEX_TABLE

    id = UnicodeAttribute(hash_key=True)
    tableTerms = UnicodeAttribute()
    tableName = UnicodeAttribute()
    columnName = UnicodeAttribute()
    term = UnicodeAttribute()
    label = UnicodeAttribute()
    type = UnicodeAttribute()
    
    termIndex = TermIndex()
    tableIndex = TableIndex()
    tableTermsIndex = TableTermsIndex()


    @classmethod
    def make_index_entry(cls, tableName, columnName, term, label, type):
        id = f'{tableName}\t{columnName}\t{term}'
        tableTerms = f'{tableName}\t{term}'
        entry = OntoData(hash_key=id)
        entry.tableName = tableName
        entry.tableTerms = tableTerms
        entry.columnName = columnName
        entry.term = term
        entry.label = label
        entry.type = type

        return entry


if __name__ == '__main__':
    pass
