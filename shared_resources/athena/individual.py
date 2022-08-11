import jsons
import boto3
import time

s3 = boto3.client('s3')
athena = boto3.client('athena')


class OntologyTerm(jsons.JsonSerializable):
    id: str
    label: str


class Individual(jsons.JsonSerializable):
    def __init__(
                self,
                *,
                id="",
                datasetIds=[],
                diseases=[],
                ethnicity={},
                exposures=[],
                geographicOrigin={},
                info={},
                interventionsOrProcedures=[],
                karyotypicSex="",
                measures=[],
                pedigrees=[],
                phenotypicFeatures=[],
                sex={},
                treatments=[]
            ):
        self.id = id
        self.datasetIds = datasetIds
        self.diseases = diseases
        self.ethnicity = ethnicity
        self.exposures = exposures
        self.geographicOrigin = geographicOrigin
        self.info = info
        self.interventionsOrProcedures = interventionsOrProcedures
        self.karyotypicSex = karyotypicSex
        self.measures = measures
        self.pedigrees = pedigrees
        self.phenotypicFeatures = phenotypicFeatures
        self.sex = sex
        self.treatments = treatments


if __name__ == '__main__':
    # response = athena.start_query_execution(
    #     QueryString='''
    #     select distinct term, label, type from (
    #     select distinct json_extract(ethnicity, '$.id') as term, json_extract(ethnicity, '$.label') as label, 'string' as type from "sbeacon-metadata"."sbeacon-individuals"
    #     union
    #     select distinct json_extract(geographicorigin, '$.id') as term, json_extract(geographicorigin, '$.label') as label, 'string' as type from "sbeacon-metadata"."sbeacon-individuals"
    #     union
    #     select distinct json_extract(sex, '$.id') as term, json_extract(sex, '$.label') as label, 'string' as type from "sbeacon-metadata"."sbeacon-individuals"
    #     );
    #     ''',
    #     # ClientRequestToken='string',
    #     QueryExecutionContext={
    #         'Database': 'sbeacon-metadata'
    #     },
    #     WorkGroup='query_workgroup'
    # )

    # retries = 0
    # while True:
    #     exec = athena.get_query_execution(
    #         QueryExecutionId=response['QueryExecutionId']
    #     )
    #     status = exec['QueryExecution']['Status']['State']
        
    #     if status in ('QUEUED', 'RUNNING'):
    #         time.sleep(0.5 * (2**retries))
    #         retries += 1
    #         continue
    #     elif status in ('FAILED', 'CANCELLED'):
    #         print('Error: ', exec['QueryExecution']['Status']['AthenaError'])
    #         break
    #     else:
    #         result = athena.get_query_results(
    #             QueryExecutionId=response['QueryExecutionId'],
    #             # NextToken='string',
    #             MaxResults=1000
    #         )
    #         print(result)
    #         break

    data = {'UpdateCount': 0, 'ResultSet': {'Rows': [{'Data': [{'VarCharValue': 'term'}, {'VarCharValue': 'label'}, {'VarCharValue': 'type'}]}, {'Data': [{'VarCharValue': '"NCIT:C43851"'}, {'VarCharValue': '"European"'}, {'VarCharValue': 'string'}]}, {'Data': [{'VarCharValue': '"NCIT:C104495"'}, {'VarCharValue': '"Other race"'}, {'VarCharValue': 'string'}]}, {'Data': [{'VarCharValue': '"NCIT:C77812"'}, {'VarCharValue': '"North American"'}, {'VarCharValue': 'string'}]}, {'Data': [{'VarCharValue': '"NCIT:C1799"'}, {'VarCharValue': '"unknown"'}, {'VarCharValue': 'string'}]}, {'Data': [{'VarCharValue': '"GAZ:00002955"'}, {'VarCharValue': '"Slovenia"'}, {'VarCharValue': 'string'}]}, {'Data': [{'VarCharValue': '"GAZ:00002459"'}, {'VarCharValue': '"United States of America"'}, {'VarCharValue': 'string'}]}, {'Data': [{'VarCharValue': '"NCIT:C20197"'}, {'VarCharValue': '"male"'}, {'VarCharValue': 'string'}]}, {'Data': [{'VarCharValue': '"NCIT:C126535"'}, {'VarCharValue': '"Australian"'}, {'VarCharValue': 'string'}]}, {'Data': [{'VarCharValue': '"NCIT:C16576"'}, {'VarCharValue': '"female"'}, {'VarCharValue': 'string'}]}, {'Data': [{'VarCharValue': '"NCIT:C42331"'}, {'VarCharValue': '"African"'}, {'VarCharValue': 'string'}]}, {'Data': [{'VarCharValue': '"NCIT:C126531"'}, {'VarCharValue': '"Latin American"'}, {'VarCharValue': 'string'}]}, {'Data': [{'VarCharValue': '"NCIT:C41260"'}, {'VarCharValue': '"Asian"'}, {'VarCharValue': 'string'}]}, {'Data': [{'VarCharValue': '"GAZ:00316959"'}, {'VarCharValue': '"Municipality of El Masnou"'}, {'VarCharValue': 'string'}]}, {'Data': [{'VarCharValue': '"GAZ:00000460"'}, {'VarCharValue': '"Eurasia"'}, {'VarCharValue': 'string'}]}], 'ResultSetMetadata': {'ColumnInfo': [{'CatalogName': 'hive', 'SchemaName': '', 'TableName': '', 'Name': 'term', 'Label': 'term', 'Type': 'json', 'Precision': 0, 'Scale': 0, 'Nullable': 'UNKNOWN', 'CaseSensitive': False}, {'CatalogName': 'hive', 'SchemaName': '', 'TableName': '', 'Name': 'label', 'Label': 'label', 'Type': 'json', 'Precision': 0, 'Scale': 0, 'Nullable': 'UNKNOWN', 'CaseSensitive': False}, {'CatalogName': 'hive', 'SchemaName': '', 'TableName': '', 'Name': 'type', 'Label': 'type', 'Type': 'varchar', 'Precision': 6, 'Scale': 0, 'Nullable': 'UNKNOWN', 'CaseSensitive': True}]}}, 'ResponseMetadata': {'RequestId': 'f6a2c077-951a-4a19-b228-5b0ba9b9ea44', 'HTTPStatusCode': 200, 'HTTPHeaders': {'content-type': 'application/x-amz-json-1.1', 'date': 'Thu, 11 Aug 2022 03:33:37 GMT', 'x-amzn-requestid': 'f6a2c077-951a-4a19-b228-5b0ba9b9ea44', 'content-length': '3501', 'connection': 'keep-alive'}, 'RetryAttempts': 0}}
    for row in data['ResultSet']['Rows'][1:]:
        term, label, typ = row['Data']
        term, label, typ = term['VarCharValue'], label['VarCharValue'], typ['VarCharValue']
