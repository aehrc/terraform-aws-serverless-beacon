## Generating the Indexer Query

The python script `generate_query.py` creates the query that resides inside the file `helper_queries.sql`. STDOUT from the python script can be directly written into this SQL file.

### TODOs

Currently the SQL query only reads the JSON path `$.id`. However, this needs to be updated and appropriate JSON paths for a given column must be recorded. This will extend the querying capabilities to handle JSON Array structures and multi schema json objects.