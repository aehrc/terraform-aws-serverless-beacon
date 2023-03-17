QUERY = """
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
SELECT DISTINCT term, label, type, kind FROM "{table}"
ORDER BY term 
ASC;
"""
