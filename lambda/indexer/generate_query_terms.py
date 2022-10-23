QUERY = '''
CREATE TABLE sbeacon_terms
WITH (
    format = 'ORC',
    write_compression = 'SNAPPY',
    external_location = '{uri}',
    partitioned_by = ARRAY['kind'], 
    bucketed_by = ARRAY['term'],
    bucket_count = 15
)
AS
SELECT DISTINCT term, label, type, kind
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
        '{kind}' AS kind
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


def get_ctas_terms_query(uri):
    subquery = ''
    for table, column_data in query_sets.items():
        for column, id_path, label_path, type_path in column_data:
            subquery += SUBQUERY.format(
                column=column, 
                table=table,
                kind=table.replace('sbeacon_', ''),
                id_path=id_path,
                label_path=label_path,
                type_path=type_path
            )
    query = QUERY.format(uri=uri, subquery=subquery.strip('\n').strip('UNION').rstrip()).strip()
    return query


if __name__ == '__main__':
    import os
    print(get_ctas_terms_query(f"s3://{os.environ['METADATA_BUCKET']}/terms/"))
