#
# submitDataset Lambda Function
#
resource "aws_lambda_function" "submitDataset" {
  function_name = "submitDataset"
  description = "Creates or updates a dataset and triggers summariseVcf."
  role = "${aws_iam_role.lambda-submitDataset.arn}"
  handler = "lambda_function.lambda_handler"
  runtime = "python3.6"
  memory_size = 2048
  timeout = 5
  tracing_config {
    mode = "Active"
  }

  s3_bucket = "${aws_s3_bucket.lambda-packages.bucket}"
  s3_key = "${aws_s3_bucket_object.submitDataset-package.id}"
  source_code_hash = "${base64sha256(file(aws_s3_bucket_object.submitDataset-package.source))}"

  environment {
    variables = {
      DATASETS_TABLE = "${aws_dynamodb_table.datasets.name}"
      VCF_SUMMARIES_TABLE = "${aws_dynamodb_table.vcf_summaries.name}"
    }
  }
}

resource "aws_lambda_permission" "APISubmitDataset" {
  statement_id = "AllowAPISubmitDatasetInvoke"
  action = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.submitDataset.function_name}"
  principal = "apigateway.amazonaws.com"
  source_arn = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.submit.path_part}"
}

#
# summariseVcf Lambda Function
#
resource "aws_lambda_function" "summariseVcf" {
  function_name = "summariseVcf"
  description = "Calculates information in a vcf and saves it in datasets dynamoDB."
  role = "${aws_iam_role.lambda-summariseVcf.arn}"
  handler = "lambda_function.lambda_handler"
  runtime = "python3.6"
  memory_size = 2048
  timeout = 300
  tracing_config {
    mode = "Active"
  }

  s3_bucket = "${aws_s3_bucket.lambda-packages.bucket}"
  s3_key = "${aws_s3_bucket_object.summariseVcf-package.id}"
  source_code_hash = "${base64sha256(file(aws_s3_bucket_object.summariseVcf-package.source))}"

  environment {
    variables = {
      DATASETS_TABLE = "${aws_dynamodb_table.datasets.name}"
    }
  }
}

resource "aws_lambda_permission" "SNSSummariseVcf" {
  statement_id = "AllowSNSSummariseVcfInvoke"
  action = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.summariseVcf.function_name}"
  principal = "sns.amazonaws.com"
  source_arn = "${aws_sns_topic.updateDataset.arn}"
}

#
# queryDatasets Lambda Function
#
resource "aws_lambda_function" "queryDatasets" {
  function_name = "queryDatasets"
  description = "Invokes splitQuery for each dataset and returns result."
  role = "${aws_iam_role.lambda-queryDatasets.arn}"
  handler = "lambda_function.lambda_handler"
  runtime = "python3.6"
  memory_size = 2048
  timeout = 28
  tracing_config {
    mode = "Active"
  }

  s3_bucket = "${aws_s3_bucket.lambda-packages.bucket}"
  s3_key = "${aws_s3_bucket_object.queryDatasets-package.id}"
  source_code_hash = "${base64sha256(file(aws_s3_bucket_object.queryDatasets-package.source))}"

  environment {
    variables = {
      BEACON_ID = "${var.beacon-id}"
      DATASETS_TABLE = "${aws_dynamodb_table.datasets.name}"
      SPLIT_QUERY_LAMBDA = "${aws_lambda_function.splitQuery.function_name}"
    }
  }
}

resource "aws_lambda_permission" "APIQueryDatasets" {
  statement_id = "AllowAPIQueryDatasetsInvoke"
  action = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.queryDatasets.function_name}"
  principal = "apigateway.amazonaws.com"
  source_arn = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.query.path_part}"
}

#
# splitQuery Lambda Function
#
resource "aws_lambda_function" "splitQuery" {
  function_name = "splitQuery"
  description = "Splits a dataset into smaller slices of VCFs and invokes performQuery on each."
  role = "${aws_iam_role.lambda-splitQuery.arn}"
  handler = "lambda_function.lambda_handler"
  runtime = "python3.6"
  memory_size = 2048
  timeout = 26
  tracing_config {
    mode = "Active"
  }

  s3_bucket = "${aws_s3_bucket.lambda-packages.bucket}"
  s3_key = "${aws_s3_bucket_object.splitQuery-package.id}"
  source_code_hash = "${base64sha256(file(aws_s3_bucket_object.splitQuery-package.source))}"

  environment {
    variables = {
      PERFORM_QUERY_LAMBDA = "${aws_lambda_function.performQuery.function_name}"
    }
  }
}

resource "aws_lambda_permission" "QueryDatasetsLambdaSplitQuery" {
  statement_id = "AllowQueryDatasetsLambdaSplitQueryInvoke"
  action = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.splitQuery.function_name}"
  principal = "lambda.amazonaws.com"
  source_arn = "${aws_lambda_function.queryDatasets.arn}"
}

#
# performQuery Lambda Function
#
resource "aws_lambda_function" "performQuery" {
  function_name = "performQuery"
  description = "Queries a slice of a vcf for a specified variant."
  role = "${aws_iam_role.lambda-performQuery.arn}"
  handler = "lambda_function.lambda_handler"
  runtime = "python3.6"
  memory_size = 2048
  timeout = 24
  tracing_config {
    mode = "Active"
  }

  s3_bucket = "${aws_s3_bucket.lambda-packages.bucket}"
  s3_key = "${aws_s3_bucket_object.performQuery-package.id}"
  source_code_hash = "${base64sha256(file(aws_s3_bucket_object.performQuery-package.source))}"
}

resource "aws_lambda_permission" "SplitQueryLambdaPerformQuery" {
  statement_id = "AllowSplitQueryLambdaPerformQueryInvoke"
  action = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.performQuery.function_name}"
  principal = "lambda.amazonaws.com"
  source_arn = "${aws_lambda_function.splitQuery.arn}"
}
