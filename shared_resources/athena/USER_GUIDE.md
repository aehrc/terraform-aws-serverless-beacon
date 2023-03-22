## Comprehensive user guide

Refer to the user guide here: https://hands-on.cloud/working-with-athena-in-python-using-boto3/

## Notes

If you manually add data as file uploads to athena, you must run the crawler. It indexes the column names (as column order may vary during ORC creation). Running the crawler costs and not suitable for development as crawling needed after every deployment. Because;

> Running crawler reorganise the column order, which resets when we `terraform apply`.

Manual uploads must be avoided at all costs, unless you upload column ordered ORCs!
Once you upload the ORCs, if they have partitions, crawler must be run again to build the partition index.
To avoid this you can run `MSCK REPAIR TABLE <table_name>;` from console. This will update the partitions from s3.

> No caution needed when added data via SQL!

Read more hacks: https://stackoverflow.com/a/58052145/4080504
