QUERY = """
CREATE TABLE sbeacon_terms_index
WITH (
    format = 'ORC',
    write_compression = 'SNAPPY',
    external_location = '{uri}',
    partitioned_by = ARRAY['kind'], 
    bucketed_by = ARRAY['term'],
    bucket_count = 50
)
AS
SELECT id, term, kind FROM "{table}";
"""
