SELECT DISTINCT term, label, type, tablename, colname
FROM (
    SELECT DISTINCT
        JSON_EXTRACT_SCALAR(ethnicity, '$.id') AS term, 
        JSON_EXTRACT_SCALAR(ethnicity, '$.label') AS label,
        COALESCE(NULLIF(JSON_EXTRACT_SCALAR(ethnicity, '$.type'), ''), 'string') AS type,
        'sbeacon_individuals' as tablename,
        'ethnicity' as colname
    FROM "sbeacon_individuals"
    WHERE JSON_EXTRACT_SCALAR(ethnicity, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        JSON_EXTRACT_SCALAR(geographicorigin, '$.id') AS term, 
        JSON_EXTRACT_SCALAR(geographicorigin, '$.label') AS label,
        COALESCE(NULLIF(JSON_EXTRACT_SCALAR(geographicorigin, '$.type'), ''), 'string') AS type,
        'sbeacon_individuals' as tablename,
        'geographicorigin' as colname
    FROM "sbeacon_individuals"
    WHERE JSON_EXTRACT_SCALAR(geographicorigin, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        JSON_EXTRACT_SCALAR(sex, '$.id') AS term, 
        JSON_EXTRACT_SCALAR(sex, '$.label') AS label,
        COALESCE(NULLIF(JSON_EXTRACT_SCALAR(sex, '$.type'), ''), 'string') AS type,
        'sbeacon_individuals' as tablename,
        'sex' as colname
    FROM "sbeacon_individuals"
    WHERE JSON_EXTRACT_SCALAR(sex, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        JSON_EXTRACT_SCALAR(biosamplestatus, '$.id') AS term, 
        JSON_EXTRACT_SCALAR(biosamplestatus, '$.label') AS label,
        COALESCE(NULLIF(JSON_EXTRACT_SCALAR(biosamplestatus, '$.type'), ''), 'string') AS type,
        'sbeacon_biosamples' as tablename,
        'biosamplestatus' as colname
    FROM "sbeacon_biosamples"
    WHERE JSON_EXTRACT_SCALAR(biosamplestatus, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        JSON_EXTRACT_SCALAR(histologicaldiagnosis, '$.id') AS term, 
        JSON_EXTRACT_SCALAR(histologicaldiagnosis, '$.label') AS label,
        COALESCE(NULLIF(JSON_EXTRACT_SCALAR(histologicaldiagnosis, '$.type'), ''), 'string') AS type,
        'sbeacon_biosamples' as tablename,
        'histologicaldiagnosis' as colname
    FROM "sbeacon_biosamples"
    WHERE JSON_EXTRACT_SCALAR(histologicaldiagnosis, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        JSON_EXTRACT_SCALAR(obtentionprocedure, '$.id') AS term, 
        JSON_EXTRACT_SCALAR(obtentionprocedure, '$.label') AS label,
        COALESCE(NULLIF(JSON_EXTRACT_SCALAR(obtentionprocedure, '$.type'), ''), 'string') AS type,
        'sbeacon_biosamples' as tablename,
        'obtentionprocedure' as colname
    FROM "sbeacon_biosamples"
    WHERE JSON_EXTRACT_SCALAR(obtentionprocedure, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        JSON_EXTRACT_SCALAR(pathologicalstage, '$.id') AS term, 
        JSON_EXTRACT_SCALAR(pathologicalstage, '$.label') AS label,
        COALESCE(NULLIF(JSON_EXTRACT_SCALAR(pathologicalstage, '$.type'), ''), 'string') AS type,
        'sbeacon_biosamples' as tablename,
        'pathologicalstage' as colname
    FROM "sbeacon_biosamples"
    WHERE JSON_EXTRACT_SCALAR(pathologicalstage, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        JSON_EXTRACT_SCALAR(pathologicaltnmfinding, '$.id') AS term, 
        JSON_EXTRACT_SCALAR(pathologicaltnmfinding, '$.label') AS label,
        COALESCE(NULLIF(JSON_EXTRACT_SCALAR(pathologicaltnmfinding, '$.type'), ''), 'string') AS type,
        'sbeacon_biosamples' as tablename,
        'pathologicaltnmfinding' as colname
    FROM "sbeacon_biosamples"
    WHERE JSON_EXTRACT_SCALAR(pathologicaltnmfinding, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        JSON_EXTRACT_SCALAR(sampleorigindetail, '$.id') AS term, 
        JSON_EXTRACT_SCALAR(sampleorigindetail, '$.label') AS label,
        COALESCE(NULLIF(JSON_EXTRACT_SCALAR(sampleorigindetail, '$.type'), ''), 'string') AS type,
        'sbeacon_biosamples' as tablename,
        'sampleorigindetail' as colname
    FROM "sbeacon_biosamples"
    WHERE JSON_EXTRACT_SCALAR(sampleorigindetail, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        JSON_EXTRACT_SCALAR(sampleorigintype, '$.id') AS term, 
        JSON_EXTRACT_SCALAR(sampleorigintype, '$.label') AS label,
        COALESCE(NULLIF(JSON_EXTRACT_SCALAR(sampleorigintype, '$.type'), ''), 'string') AS type,
        'sbeacon_biosamples' as tablename,
        'sampleorigintype' as colname
    FROM "sbeacon_biosamples"
    WHERE JSON_EXTRACT_SCALAR(sampleorigintype, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        JSON_EXTRACT_SCALAR(sampleprocessing, '$.id') AS term, 
        JSON_EXTRACT_SCALAR(sampleprocessing, '$.label') AS label,
        COALESCE(NULLIF(JSON_EXTRACT_SCALAR(sampleprocessing, '$.type'), ''), 'string') AS type,
        'sbeacon_biosamples' as tablename,
        'sampleprocessing' as colname
    FROM "sbeacon_biosamples"
    WHERE JSON_EXTRACT_SCALAR(sampleprocessing, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        JSON_EXTRACT_SCALAR(tumorprogression, '$.id') AS term, 
        JSON_EXTRACT_SCALAR(tumorprogression, '$.label') AS label,
        COALESCE(NULLIF(JSON_EXTRACT_SCALAR(tumorprogression, '$.type'), ''), 'string') AS type,
        'sbeacon_biosamples' as tablename,
        'tumorprogression' as colname
    FROM "sbeacon_biosamples"
    WHERE JSON_EXTRACT_SCALAR(tumorprogression, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        JSON_EXTRACT_SCALAR(librarysource, '$.id') AS term, 
        JSON_EXTRACT_SCALAR(librarysource, '$.label') AS label,
        COALESCE(NULLIF(JSON_EXTRACT_SCALAR(librarysource, '$.type'), ''), 'string') AS type,
        'sbeacon_runs' as tablename,
        'librarysource' as colname
    FROM "sbeacon_runs"
    WHERE JSON_EXTRACT_SCALAR(librarysource, '$.id') 
    IS NOT NULL
    UNION

    SELECT DISTINCT
        JSON_EXTRACT_SCALAR(platformmodel, '$.id') AS term, 
        JSON_EXTRACT_SCALAR(platformmodel, '$.label') AS label,
        COALESCE(NULLIF(JSON_EXTRACT_SCALAR(platformmodel, '$.type'), ''), 'string') AS type,
        'sbeacon_runs' as tablename,
        'platformmodel' as colname
    FROM "sbeacon_runs"
    WHERE JSON_EXTRACT_SCALAR(platformmodel, '$.id') 
    IS NOT NULL
) 
ORDER BY term 
ASC;
