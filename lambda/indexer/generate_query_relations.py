QUERY = '''
CREATE TABLE sbeacon_relations
WITH (
    format = 'ORC',
    write_compression = 'SNAPPY',
    external_location = '{uri}',
    bucketed_by = ARRAY['individualid', 'biosampleid', 'runid', 'analysisid'],
    bucket_count = 25
) 
AS
SELECT 
    I._datasetid as datasetid,
    I._cohortid as cohortid,
    I.id AS individualid, 
    B.id AS biosampleid, 
    R.id AS runid,  
    A.id AS analysisid
FROM 
        "{individuals_table}" I
    JOIN "{biosamples_table}" B
        ON I.id = B."individualid"
    JOIN "{runs_table}" R
        ON B.id = R."biosampleid"
    JOIN "{analyses_table}" A
        ON R.id = A."runid"
'''
