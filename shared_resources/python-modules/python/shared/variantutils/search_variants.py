from datetime import datetime, timezone
import time
import boto3

from shared.utils import ENV_ATHENA


ATHENA_DATABASE = ENV_ATHENA.ATHENA_GENOTYPES_TABLE
ATHENA_OUTPUT_LOCATION = f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/query-results"


athena = boto3.client("athena")
s3 = boto3.client("s3")


def snp_query(
    reference_name,
    start_min,
    start_max,
    end_min,
    end_max,
    reference_bases,
    alternate_bases,
    include_samples=False
):
    if include_samples:
        join = """
        JOIN sbeacon_genotypes_cache G
        ON SNP.id = G.id_ref
        """
        select = "G.id_ref"
    else:
        join = ""
        select = "SNP.id"

    sql = f"""
    SELECT {select}
    FROM sbeacon_snps_cache SNP
    {join}
    WHERE SNP.chromosome = '{reference_name}'
    AND SNP.coordinate >= {start_min} AND SNP.coordinate <= {start_max}
    AND SNP.coordinate <= {end_min} AND SNP.coordinate <= {end_max}
    AND SNP.allelea_top_base = '{reference_bases or 'N'}'
    AND SNP.alleleb_top_base = '{alternate_bases or 'N'}'
    """

    return sql


def perform_variant_search(
    *,
    reference_name,
    reference_bases,
    alternate_bases,
    start,
    end,
    include_datasets="ALL",
    query_id="TEST",
    include_samples=False,
):
    try:
        if len(start) == 2:
            start_min, start_max = start
        else:
            start_min = start[0]

        if len(end) == 2:
            end_min, end_max = end
        else:
            end_min = start_min
            end_max = end[0]

        if len(start) != 2:
            start_max = end_max

        # Adjust for 0-based indexing
        start_min += 1
        start_max += 1
        end_min += 1
        end_max += 1


        # Build Athena SQL query
        sql = snp_query(reference_name, start_min, start_max, end_min, end_max, reference_bases, alternate_bases, include_samples)


        response = athena.start_query_execution(
            QueryString=sql,
            QueryExecutionContext={"Database": ENV_ATHENA.ATHENA_METADATA_DATABASE},
            WorkGroup=ENV_ATHENA.ATHENA_WORKGROUP,
        )


        retries = 0
        while True:
            exec = athena.get_query_execution(QueryExecutionId=response["QueryExecutionId"])
            status = exec["QueryExecution"]["Status"]["State"]

            if status in ("QUEUED", "RUNNING"):
                time.sleep(0.1)
                retries += 1

                if retries == 300:
                    print("Timed out")
                    return None
                continue
            elif status in ("FAILED", "CANCELLED"):
                print("Error: ", exec["QueryExecution"]["Status"])
                return None
            else:
                data = athena.get_query_results(
                    QueryExecutionId=response["QueryExecutionId"], MaxResults=1000
                )

            rows = data["ResultSet"]["Rows"]

            ids = [
                row["Data"][0]["VarCharValue"]
                for row in rows[1:]      # Skip header row
            ]

            print(ids)

            return ids


    except Exception as e:
        print(f"Error occurred: {e}")
        raise e


if __name__ == "__main__":
    pass
