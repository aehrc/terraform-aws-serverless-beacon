locals {
  api_version = "v2.0.0"
  version = "v0.0.1"
  build_cpp_path = abspath("${path.module}/build_cpp.sh")
  build_cpp_path2 = abspath("${path.module}/build_cpp2.sh")
  build_share_path = abspath("${path.module}/lambda/shared/source")
  build_gzip_path = abspath("${path.module}/lambda/shared/gzip")

  maximum_load_file_size  = 750000000
  vcf_processed_file_size = 50000000

  # lambda ARNs for invokation
  INDEXER_LAMBDA = module.lambda-indexer.lambda_function_name
  # TODO use the following organisation to refactor the IAM policy assignment
  # this makes the code simpler
  # sbeacon info variables
  sbeacon_variables = {
    BEACON_API_VERSION = local.api_version
    BEACON_ID = var.beacon-id
  }
  # athena related variables
  athena_variables = {
    ATHENA_WORKGROUP = aws_athena_workgroup.sbeacon-workgroup.name
    METADATA_DATABASE = aws_glue_catalog_database.metadata-database.name
    METADATA_BUCKET = aws_s3_bucket.metadata-bucket.bucket
    INDIVIDUALS_TABLE = aws_glue_catalog_table.sbeacon-individuals.name
    BIOSAMPLES_TABLE = aws_glue_catalog_table.sbeacon-biosamples.name
  }
  # layers
  binaries_layer = "${aws_lambda_layer_version.binaries_layer.layer_arn}:${aws_lambda_layer_version.binaries_layer.version}"
  python_libraries_layer = module.python_libraries_layer.lambda_layer_arn
}

#
# submitDataset Lambda Function
#
module "lambda-submitDataset" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "submitDataset"
  description = "Creates or updates a dataset and triggers summariseVcf."
  handler = "lambda_function.lambda_handler"
  runtime = "python3.9"
  architectures = ["x86_64"]
  memory_size = 128
  timeout = 900
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-submitDataset.json,
    data.aws_iam_policy_document.athena-full-access.json
  ]
  number_of_policy_jsons = 2
  source_path = "${path.module}/lambda/submitDataset"

  tags = var.common-tags

  environment_variables = merge(
    {
      DATASETS_TABLE = aws_dynamodb_table.datasets.name
      SUMMARISE_DATASET_SNS_TOPIC_ARN = aws_sns_topic.summariseDataset.arn
      INDEXER_LAMBDA = local.INDEXER_LAMBDA
    }, 
    local.sbeacon_variables, 
    local.athena_variables
  )
  
  layers = [
    local.python_libraries_layer,
    local.binaries_layer
  ]
}

#
# summariseDataset Lambda Function
#
module "lambda-summariseDataset" {
  source = "github.com/bhosking/terraform-aws-lambda"

  function_name = "summariseDataset"
  description = "Calculates summary counts for a dataset."
  handler = "lambda_function.lambda_handler"
  runtime = "python3.9"
  memory_size = 128
  timeout = 900
  policy = {
    json = data.aws_iam_policy_document.lambda-summariseDataset.json
  }
  source_path = "${path.module}/lambda/summariseDataset"
  tags = var.common-tags

  environment = {
    variables = {
      DATASETS_TABLE = aws_dynamodb_table.datasets.name
      SUMMARISE_VCF_SNS_TOPIC_ARN = aws_sns_topic.summariseVcf.arn
      VCF_SUMMARIES_TABLE = aws_dynamodb_table.vcf_summaries.name
      VARIANT_DUPLICATES_TABLE = aws_dynamodb_table.variant_duplicates.name
      DUPLICATE_VARIANT_SEARCH_SNS_TOPIC_ARN = aws_sns_topic.duplicateVariantSearch.arn
      VARIANTS_BUCKET = aws_s3_bucket.variants-bucket.bucket
      ABS_MAX_DATA_SPLIT = local.maximum_load_file_size
    }
  }
}

#
# summariseVcf Lambda Function
#
module "lambda-summariseVcf" {
  source = "github.com/bhosking/terraform-aws-lambda"

  function_name = "summariseVcf"
  description = "Calculates information in a vcf and saves it in datasets dynamoDB."
  handler = "lambda_function.lambda_handler"
  runtime = "python3.9"
  memory_size = 128
  timeout = 900
  policy = {
    json = data.aws_iam_policy_document.lambda-summariseVcf.json
  }
  source_path = "${path.module}/lambda/summariseVcf"
  tags = var.common-tags

  environment = {
    variables = {
      SUMMARISE_SLICE_SNS_TOPIC_ARN = aws_sns_topic.summariseSlice.arn
      VARIANTS_BUCKET = aws_s3_bucket.variants-bucket.bucket
      VCF_SUMMARIES_TABLE = aws_dynamodb_table.vcf_summaries.name
    }
  }
}

#
# summariseSlice Lambda Function
#
module "lambda-summariseSlice" {
  source = "github.com/bhosking/terraform-aws-lambda"

  function_name = "summariseSlice"
  description = "Counts calls and variants in region of a vcf."
  handler = "function"
  runtime = "provided"
  architectures = ["x86_64"]
  memory_size = 1500
  timeout = 900
  policy = {
    json = data.aws_iam_policy_document.lambda-summariseSlice.json
  }
  source_path = "${path.module}/lambda/summariseSlice/source"
  build_command = "${local.build_cpp_path} $source $filename"
  build_paths = [
    local.build_cpp_path,
    local.build_share_path,
    local.build_gzip_path,
  ]
  tags = var.common-tags

  environment = {
    variables = {
      ASSEMBLY_GSI = "${[for gsi in aws_dynamodb_table.datasets.global_secondary_index : gsi.name][0]}"
      DATASETS_TABLE = aws_dynamodb_table.datasets.name
      SUMMARISE_DATASET_SNS_TOPIC_ARN = aws_sns_topic.summariseDataset.arn
      SUMMARISE_SLICE_SNS_TOPIC_ARN = aws_sns_topic.summariseSlice.arn
      VCF_SUMMARIES_TABLE = aws_dynamodb_table.vcf_summaries.name
      VARIANTS_BUCKET = aws_s3_bucket.variants-bucket.bucket
      MAX_SLICE_GAP = 100000
      VCF_S3_OUTPUT_SIZE_LIMIT = local.vcf_processed_file_size
    }
  }
}

#
# duplicateVariantSearch Lambda Function
#
module "lambda-duplicateVariantSearch" {
  source = "github.com/bhosking/terraform-aws-lambda"

  function_name = "duplicateVariantSearch"
  description = "Searches for duplicate variants across vcfs."
  handler = "function"
  runtime = "provided"
  architectures = ["x86_64"]
  memory_size = 5000
  timeout = 900
  policy = {
    json = data.aws_iam_policy_document.lambda-duplicateVariantSearch.json
  }
  source_path = "${path.module}/lambda/duplicateVariantSearch/source"
  build_command = "${local.build_cpp_path} $source $filename"
  build_paths = [
    local.build_cpp_path,
    local.build_share_path,
    local.build_gzip_path,
  ]
  tags = var.common-tags

  environment = {
    variables = {
      ASSEMBLY_GSI = "${[for gsi in aws_dynamodb_table.datasets.global_secondary_index : gsi.name][0]}"
      VARIANT_DUPLICATES_TABLE = aws_dynamodb_table.variant_duplicates.name
      DATASETS_TABLE = aws_dynamodb_table.datasets.name
    }
  }
}

# Following is just a template for c++ codes using latest terraform module
module "lambda_functionDVS" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "duplicateVariantSearchDVS"
  description = "Searches for duplicate variants across vcfs."
  handler = "function"
  runtime = "provided"
  architectures = ["x86_64"]
  memory_size = 1536
  timeout = 900
  attach_policy_json = true
  policy_json =  data.aws_iam_policy_document.lambda-duplicateVariantSearch.json

  source_path = [
    {
      path     = "${path.module}/lambda/duplicateVariantSearchDVS",
      commands = [
        "sh ${local.build_cpp_path2} ./",
        "cd build/function_binaries",
        ":zip"
      ],
      patterns = [
        "source/*",
      ]
    }
  ]

  tags = var.common-tags

  environment_variables = {
    ASSEMBLY_GSI = "${[for gsi in aws_dynamodb_table.datasets.global_secondary_index : gsi.name][0]}"
    VARIANT_DUPLICATES_TABLE = aws_dynamodb_table.variant_duplicates.name
    DATASETS_TABLE = aws_dynamodb_table.datasets.name
  }
}

#
# getInfo Lambda Function
#
module "lambda-getInfo" {
  source = "github.com/bhosking/terraform-aws-lambda"

  function_name = "getInfo"
  description = "Returns basic information about the beacon and the datasets."
  handler = "lambda_function.lambda_handler"
  runtime = "python3.9"
  memory_size = 128
  timeout = 900
  policy = {
    json = data.aws_iam_policy_document.lambda-getInfo.json
  }
  source_path = "${path.module}/lambda/getInfo"
  tags = var.common-tags

  environment = {
    variables = {
      BEACON_API_VERSION = local.api_version
      VERSION = local.version
      BEACON_ID = var.beacon-id
      BEACON_NAME = var.beacon-name
      DATASETS_TABLE = aws_dynamodb_table.datasets.name
      ORGANISATION_ID = var.organisation-id
      ORGANISATION_NAME = var.organisation-name
    }
  }
}

#
# getConfiguration Lambda Function
#
module "lambda-getConfiguration" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "getConfiguration"
  description = "Get the beacon configuration."
  runtime = "python3.9"
  handler = "lambda_function.lambda_handler"
  memory_size = 128
  timeout = 900
  attach_policy_json = true
  policy_json = data.aws_iam_policy_document.lambda-getConfiguration.json
  source_path = "${path.module}/lambda/getConfiguration"

  tags = var.common-tags

  environment_variables = {
    BEACON_API_VERSION = local.api_version
  }
}

#
# getMap Lambda Function
#
module "lambda-getMap" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "getMap"
  description = "Get the beacon map."
  runtime = "python3.9"
  handler = "lambda_function.lambda_handler"
  memory_size = 128
  timeout = 900
  attach_policy_json = true
  policy_json = data.aws_iam_policy_document.lambda-getMap.json
  source_path = "${path.module}/lambda/getMap"

  tags = var.common-tags

  environment_variables = local.sbeacon_variables
}

#
# getEntryTypes Lambda Function
#
module "lambda-getEntryTypes" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "getEntryTypes"
  description = "Get the beacon map."
  runtime = "python3.9"
  handler = "lambda_function.lambda_handler"
  memory_size = 128
  timeout = 900
  attach_policy_json = true
  policy_json = data.aws_iam_policy_document.lambda-getEntryTypes.json
  source_path = "${path.module}/lambda/getEntryTypes"

  tags = var.common-tags

  environment_variables = {
    BEACON_API_VERSION = local.api_version
  }
}

#
# getFilteringTerms Lambda Function
#
module "lambda-getFilteringTerms" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "getFilteringTerms"
  description = "Get the beacon map."
  runtime = "python3.9"
  handler = "lambda_function.lambda_handler"
  memory_size = 128
  timeout = 900
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-getFilteringTerms.json,
    data.aws_iam_policy_document.athena-full-access.json
  ]
  number_of_policy_jsons = 2
  source_path = "${path.module}/lambda/getFilteringTerms"

  tags = var.common-tags

  environment_variables = merge(
    local.sbeacon_variables,
    local.athena_variables
  )

  layers = [
    local.python_libraries_layer
  ]
}

#
# getAnalyses Lambda Function
#
module "lambda-getAnalyses" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "getAnalyses"
  description = "Get the beacon map."
  runtime = "python3.9"
  handler = "lambda_function.lambda_handler"
  memory_size = 128
  timeout = 900
  attach_policy_json = true
  policy_json = data.aws_iam_policy_document.lambda-getAnalyses.json
  source_path = "${path.module}/lambda/getAnalyses"

  tags = var.common-tags

  environment_variables = {
    BEACON_API_VERSION = local.api_version
    BEACON_ID = var.beacon-id
  }
}

#
# getGenomicVariants Lambda Function
#
module "lambda-getGenomicVariants" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "getGenomicVariants"
  description = "Get the variants."
  runtime = "python3.9"
  handler = "lambda_function.lambda_handler"
  memory_size = 128
  timeout = 900
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-getGenomicVariants.json,
    data.aws_iam_policy_document.athena-full-access.json
  ]
  number_of_policy_jsons = 2
  source_path = "${path.module}/lambda/getGenomicVariants"

  tags = var.common-tags

  environment_variables = merge(
    {
      DATASETS_TABLE = aws_dynamodb_table.datasets.name
      QUERIES_TABLE = aws_dynamodb_table.variant_queries.name
      VARIANT_QUERY_RESPONSES_TABLE = aws_dynamodb_table.variant_query_responses.name
      SPLIT_QUERY_LAMBDA = module.lambda-splitQuery.function_name
      PERFORM_QUERY_LAMBDA = module.lambda-performQuery.function_name
    },
    local.athena_variables,
    local.sbeacon_variables
  )

  layers = [
    local.python_libraries_layer
  ]
}

#
# getIndividuals Lambda Function
#
module "lambda-getIndividuals" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "getIndividuals"
  description = "Get the individuals."
  runtime = "python3.9"
  handler = "lambda_function.lambda_handler"
  memory_size = 128
  timeout = 900
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-getIndividuals.json,
    data.aws_iam_policy_document.athena-full-access.json
  ]
  number_of_policy_jsons = 2
  source_path = "${path.module}/lambda/getIndividuals"

  tags = var.common-tags

  environment_variables = merge(
    {
      DATASETS_TABLE = aws_dynamodb_table.datasets.name
      QUERIES_TABLE = aws_dynamodb_table.variant_queries.name
      VARIANT_QUERY_RESPONSES_TABLE = aws_dynamodb_table.variant_query_responses.name
      SPLIT_QUERY_LAMBDA = module.lambda-splitQuery.function_name
      PERFORM_QUERY_LAMBDA = module.lambda-performQuery.function_name
    },
    local.athena_variables,
    local.sbeacon_variables
  )

  layers = [
    local.python_libraries_layer
  ]
}

#
# splitQuery Lambda Function
#
module "lambda-splitQuery" {
  source = "github.com/bhosking/terraform-aws-lambda"

  function_name = "splitQuery"
  description = "Splits a dataset into smaller slices of VCFs and invokes performQuery on each."
  handler = "lambda_function.lambda_handler"
  runtime = "python3.9"
  memory_size = 128
  timeout = 26
  policy = {
    json = data.aws_iam_policy_document.lambda-splitQuery.json
  }
  source_path = "${path.module}/lambda/splitQuery"
  tags = var.common-tags

  environment = {
    variables = {
      PERFORM_QUERY_LAMBDA = module.lambda-performQuery.function_name
    }
  }

  layers = [
    local.python_libraries_layer
  ]
}

#
# performQuery Lambda Function
#
module "lambda-performQuery" {
  source = "github.com/bhosking/terraform-aws-lambda"

  function_name = "performQuery"
  description = "Queries a slice of a vcf for a specified variant."
  handler = "lambda_function.lambda_handler"
  runtime = "python3.9"
  memory_size = 128
  timeout = 24
  policy = {
    json = data.aws_iam_policy_document.lambda-performQuery.json
  }
  source_path = "${path.module}/lambda/performQuery"
  tags = var.common-tags

  layers = [
    local.binaries_layer,
    local.python_libraries_layer
  ]

  environment = {
    variables = {
      DATASETS_TABLE = aws_dynamodb_table.datasets.name
      QUERIES_TABLE = aws_dynamodb_table.variant_queries.name
      VARIANT_QUERY_RESPONSES_TABLE = aws_dynamodb_table.variant_query_responses.name
      BEACON_API_VERSION = local.api_version
      VARIANTS_BUCKET = aws_s3_bucket.variants-bucket.bucket
    }
  }
}

#
# indexer Lambda Function
#
module "lambda-indexer" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "indexer"
  description = "Run the indexing tasks."
  runtime = "python3.9"
  handler = "lambda_function.lambda_handler"
  memory_size = 128
  timeout = 900
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.athena-full-access.json
  ]
  number_of_policy_jsons = 1
  source_path = "${path.module}/lambda/indexer"

  tags = var.common-tags

  environment_variables = merge(
    local.sbeacon_variables,
    local.athena_variables
  )

  layers = [
    local.python_libraries_layer
  ]
}
