QUERY = """
CREATE TABLE {target}
WITH (
    format = 'ORC',
    write_compression = 'SNAPPY',
    external_location = '{uri}',
    bucketed_by = ARRAY[{bucket_by}],
    bucket_count = {bucket_count}
)
AS
SELECT * FROM "{table}";
"""
