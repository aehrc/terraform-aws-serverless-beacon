CREATE TABLE sbeacon_terms_index
WITH (
    format = 'ORC',
    write_compression = 'SNAPPY',
    external_location  = 's3://sbeacon-metadata-20221005045707476400000001/terms_index/',
    partitioned_by = ARRAY['kind'], 
    bucketed_by = ARRAY['term'],
    bucket_count = 15
)
AS
SELECT * FROM (
    SELECT DISTINCT
        id,
        JSON_EXTRACT_SCALAR(ethnicity, '$.id') AS term,
        'individuals' as kind
    FROM "sbeacon_individuals"
    WHERE JSON_EXTRACT_SCALAR(ethnicity, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        id,
        JSON_EXTRACT_SCALAR(geographicorigin, '$.id') AS term,
        'individuals' as kind
    FROM "sbeacon_individuals"
    WHERE JSON_EXTRACT_SCALAR(geographicorigin, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        id,
        JSON_EXTRACT_SCALAR(sex, '$.id') AS term,
        'individuals' as kind
    FROM "sbeacon_individuals"
    WHERE JSON_EXTRACT_SCALAR(sex, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        id,
        JSON_EXTRACT_SCALAR(biosamplestatus, '$.id') AS term,
        'biosamples' as kind
    FROM "sbeacon_biosamples"
    WHERE JSON_EXTRACT_SCALAR(biosamplestatus, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        id,
        JSON_EXTRACT_SCALAR(histologicaldiagnosis, '$.id') AS term,
        'biosamples' as kind
    FROM "sbeacon_biosamples"
    WHERE JSON_EXTRACT_SCALAR(histologicaldiagnosis, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        id,
        JSON_EXTRACT_SCALAR(obtentionprocedure, '$.id') AS term,
        'biosamples' as kind
    FROM "sbeacon_biosamples"
    WHERE JSON_EXTRACT_SCALAR(obtentionprocedure, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        id,
        JSON_EXTRACT_SCALAR(pathologicalstage, '$.id') AS term,
        'biosamples' as kind
    FROM "sbeacon_biosamples"
    WHERE JSON_EXTRACT_SCALAR(pathologicalstage, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        id,
        JSON_EXTRACT_SCALAR(pathologicaltnmfinding, '$.id') AS term,
        'biosamples' as kind
    FROM "sbeacon_biosamples"
    WHERE JSON_EXTRACT_SCALAR(pathologicaltnmfinding, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        id,
        JSON_EXTRACT_SCALAR(sampleorigindetail, '$.id') AS term,
        'biosamples' as kind
    FROM "sbeacon_biosamples"
    WHERE JSON_EXTRACT_SCALAR(sampleorigindetail, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        id,
        JSON_EXTRACT_SCALAR(sampleorigintype, '$.id') AS term,
        'biosamples' as kind
    FROM "sbeacon_biosamples"
    WHERE JSON_EXTRACT_SCALAR(sampleorigintype, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        id,
        JSON_EXTRACT_SCALAR(sampleprocessing, '$.id') AS term,
        'biosamples' as kind
    FROM "sbeacon_biosamples"
    WHERE JSON_EXTRACT_SCALAR(sampleprocessing, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        id,
        JSON_EXTRACT_SCALAR(tumorprogression, '$.id') AS term,
        'biosamples' as kind
    FROM "sbeacon_biosamples"
    WHERE JSON_EXTRACT_SCALAR(tumorprogression, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        id,
        JSON_EXTRACT_SCALAR(librarysource, '$.id') AS term,
        'runs' as kind
    FROM "sbeacon_runs"
    WHERE JSON_EXTRACT_SCALAR(librarysource, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        id,
        JSON_EXTRACT_SCALAR(platformmodel, '$.id') AS term,
        'runs' as kind
    FROM "sbeacon_runs"
    WHERE JSON_EXTRACT_SCALAR(platformmodel, '$.id') 
    IS NOT NULL
);
