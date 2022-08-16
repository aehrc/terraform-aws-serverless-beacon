SELECT DISTINCT term, label, type, tablename, colname
FROM (
    SELECT DISTINCT
        CAST(JSON_EXTRACT(ethnicity, '$.id') AS varchar) AS term, 
        CAST(JSON_EXTRACT(ethnicity, '$.label') AS varchar) AS label,
        COALESCE(NULLIF(CAST(JSON_EXTRACT(ethnicity, '$.type') as varchar), ''), 'string') AS type,
        'sbeacon_individuals' as tablename,
        'ethnicity' as colname
    FROM "sbeacon_individuals"
    WHERE JSON_EXTRACT(ethnicity, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        CAST(JSON_EXTRACT(geographicorigin, '$.id') AS varchar) AS term, 
        CAST(JSON_EXTRACT(geographicorigin, '$.label') AS varchar) AS label,
        COALESCE(NULLIF(CAST(JSON_EXTRACT(geographicorigin, '$.type') as varchar), ''), 'string') AS type,
        'sbeacon_individuals' as tablename,
        'geographicorigin' as colname
    FROM "sbeacon_individuals"
    WHERE JSON_EXTRACT(geographicorigin, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        CAST(JSON_EXTRACT(sex, '$.id') AS varchar) AS term, 
        CAST(JSON_EXTRACT(sex, '$.label') AS varchar) AS label,
        COALESCE(NULLIF(CAST(JSON_EXTRACT(sex, '$.type') as varchar), ''), 'string') AS type,
        'sbeacon_individuals' as tablename,
        'sex' as colname
    FROM "sbeacon_individuals"
    WHERE JSON_EXTRACT(sex, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        CAST(JSON_EXTRACT(biosamplestatus, '$.id') AS varchar) AS term, 
        CAST(JSON_EXTRACT(biosamplestatus, '$.label') AS varchar) AS label,
        COALESCE(NULLIF(CAST(JSON_EXTRACT(biosamplestatus, '$.type') as varchar), ''), 'string') AS type,
        'sbeacon_biosamples' as tablename,
        'biosamplestatus' as colname
    FROM "sbeacon_biosamples"
    WHERE JSON_EXTRACT(biosamplestatus, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        CAST(JSON_EXTRACT(histologicaldiagnosis, '$.id') AS varchar) AS term, 
        CAST(JSON_EXTRACT(histologicaldiagnosis, '$.label') AS varchar) AS label,
        COALESCE(NULLIF(CAST(JSON_EXTRACT(histologicaldiagnosis, '$.type') as varchar), ''), 'string') AS type,
        'sbeacon_biosamples' as tablename,
        'histologicaldiagnosis' as colname
    FROM "sbeacon_biosamples"
    WHERE JSON_EXTRACT(histologicaldiagnosis, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        CAST(JSON_EXTRACT(obtentionprocedure, '$.id') AS varchar) AS term, 
        CAST(JSON_EXTRACT(obtentionprocedure, '$.label') AS varchar) AS label,
        COALESCE(NULLIF(CAST(JSON_EXTRACT(obtentionprocedure, '$.type') as varchar), ''), 'string') AS type,
        'sbeacon_biosamples' as tablename,
        'obtentionprocedure' as colname
    FROM "sbeacon_biosamples"
    WHERE JSON_EXTRACT(obtentionprocedure, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        CAST(JSON_EXTRACT(pathologicalstage, '$.id') AS varchar) AS term, 
        CAST(JSON_EXTRACT(pathologicalstage, '$.label') AS varchar) AS label,
        COALESCE(NULLIF(CAST(JSON_EXTRACT(pathologicalstage, '$.type') as varchar), ''), 'string') AS type,
        'sbeacon_biosamples' as tablename,
        'pathologicalstage' as colname
    FROM "sbeacon_biosamples"
    WHERE JSON_EXTRACT(pathologicalstage, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        CAST(JSON_EXTRACT(pathologicaltnmfinding, '$.id') AS varchar) AS term, 
        CAST(JSON_EXTRACT(pathologicaltnmfinding, '$.label') AS varchar) AS label,
        COALESCE(NULLIF(CAST(JSON_EXTRACT(pathologicaltnmfinding, '$.type') as varchar), ''), 'string') AS type,
        'sbeacon_biosamples' as tablename,
        'pathologicaltnmfinding' as colname
    FROM "sbeacon_biosamples"
    WHERE JSON_EXTRACT(pathologicaltnmfinding, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        CAST(JSON_EXTRACT(sampleorigindetail, '$.id') AS varchar) AS term, 
        CAST(JSON_EXTRACT(sampleorigindetail, '$.label') AS varchar) AS label,
        COALESCE(NULLIF(CAST(JSON_EXTRACT(sampleorigindetail, '$.type') as varchar), ''), 'string') AS type,
        'sbeacon_biosamples' as tablename,
        'sampleorigindetail' as colname
    FROM "sbeacon_biosamples"
    WHERE JSON_EXTRACT(sampleorigindetail, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        CAST(JSON_EXTRACT(sampleorigintype, '$.id') AS varchar) AS term, 
        CAST(JSON_EXTRACT(sampleorigintype, '$.label') AS varchar) AS label,
        COALESCE(NULLIF(CAST(JSON_EXTRACT(sampleorigintype, '$.type') as varchar), ''), 'string') AS type,
        'sbeacon_biosamples' as tablename,
        'sampleorigintype' as colname
    FROM "sbeacon_biosamples"
    WHERE JSON_EXTRACT(sampleorigintype, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        CAST(JSON_EXTRACT(sampleprocessing, '$.id') AS varchar) AS term, 
        CAST(JSON_EXTRACT(sampleprocessing, '$.label') AS varchar) AS label,
        COALESCE(NULLIF(CAST(JSON_EXTRACT(sampleprocessing, '$.type') as varchar), ''), 'string') AS type,
        'sbeacon_biosamples' as tablename,
        'sampleprocessing' as colname
    FROM "sbeacon_biosamples"
    WHERE JSON_EXTRACT(sampleprocessing, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        CAST(JSON_EXTRACT(tumorprogression, '$.id') AS varchar) AS term, 
        CAST(JSON_EXTRACT(tumorprogression, '$.label') AS varchar) AS label,
        COALESCE(NULLIF(CAST(JSON_EXTRACT(tumorprogression, '$.type') as varchar), ''), 'string') AS type,
        'sbeacon_biosamples' as tablename,
        'tumorprogression' as colname
    FROM "sbeacon_biosamples"
    WHERE JSON_EXTRACT(tumorprogression, '$.id') 
    IS NOT NULL
) 
ORDER BY term 
ASC;

