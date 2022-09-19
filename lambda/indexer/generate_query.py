QUERY = '''
SELECT DISTINCT term, label, type, tablename, colname
FROM (
{subquery}
) 
ORDER BY term 
ASC;
'''

SUBQUERY = '''
    SELECT DISTINCT
        JSON_EXTRACT_SCALAR({column}, '{id_path}') AS term, 
        JSON_EXTRACT_SCALAR({column}, '{label_path}') AS label,
        COALESCE(NULLIF(JSON_EXTRACT_SCALAR({column}, '{type_path}'), ''), 'string') AS type,
        '{table}' as tablename,
        '{column}' as colname
    FROM "{table}"
    WHERE JSON_EXTRACT_SCALAR({column}, '{id_path}') 
    IS NOT NULL
    UNION
'''

query_sets = {
    # columns of individuals
    'sbeacon_individuals': [
        ('ethnicity', '$.id', '$.label', '$.type'),
        ('geographicorigin', '$.id', '$.label', '$.type'),
        ('sex', '$.id', '$.label', '$.type')
    ],
    # columns of biosamples
    'sbeacon_biosamples': [
        ('biosamplestatus', '$.id', '$.label', '$.type'),
        ('histologicaldiagnosis', '$.id', '$.label', '$.type'),
        ('obtentionprocedure', '$.id', '$.label', '$.type'),
        ('pathologicalstage', '$.id', '$.label', '$.type'),
        ('pathologicaltnmfinding', '$.id', '$.label', '$.type'),
        ('sampleorigindetail', '$.id', '$.label', '$.type'),
        ('sampleorigintype', '$.id', '$.label', '$.type'),
        ('sampleprocessing', '$.id', '$.label', '$.type'),
        ('tumorprogression', '$.id', '$.label', '$.type')
    ],
    # columns of runs
    'sbeacon_runs': [
        ('librarysource', '$.id', '$.label', '$.type'),
        ('platformmodel', '$.id', '$.label', '$.type')
    ]
}


if __name__ == '__main__':
    subquery = ''
    for table, column_data in query_sets.items():
        for column, id_path, label_path, type_path in column_data:
            subquery += SUBQUERY.format(
                column=column, 
                table=table,
                id_path=id_path,
                label_path=label_path,
                type_path=type_path
            )
    query = QUERY.format(table=table, subquery=subquery.strip('\n').strip('UNION').rstrip()).strip()
    print(query)
