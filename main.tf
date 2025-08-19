provider "aws" {
  region = var.region
}

data "aws_caller_identity" "this" {}

# DOCS
# Lambda memory - https://docs.aws.amazon.com/lambda/latest/dg/configuration-function-common.html
#                 https://stackoverflow.com/questions/66522916/aws-lambda-memory-vs-cpu-configuration
#
locals {
  build_cpp_path     = abspath("${path.module}/build_cpp.sh")
  shared_source_path = abspath("${path.module}/lambda/shared/source")
  gzip_source_path   = abspath("${path.module}/lambda/shared/gzip")

  maximum_load_file_size  = 750000000
  vcf_processed_file_size = 50000000
  # TODO use the following organisation to refactor the IAM policy assignment
  # this makes the code simpler
  # sbeacon info variables
  sbeacon_variables = {
    # beacon variables
    BEACON_API_VERSION         = var.beacon-api-version
    BEACON_ID                  = var.beacon-id
    BEACON_NAME                = var.beacon-name
    BEACON_ENVIRONMENT         = var.beacon-environment
    BEACON_DESCRIPTION         = var.beacon-description
    BEACON_VERSION             = var.beacon-version
    BEACON_WELCOME_URL         = var.beacon-welcome-url
    BEACON_ALTERNATIVE_URL     = var.beacon-alternative-url
    BEACON_CREATE_DATETIME     = var.beacon-create-datetime
    BEACON_UPDATE_DATETIME     = var.beacon-update-datetime
    BEACON_HANDOVERS           = var.beacon-handovers
    BEACON_DOCUMENTATION_URL   = var.beacon-documentation-url
    BEACON_DEFAULT_GRANULARITY = var.beacon-default-granularity
    BEACON_URI                 = var.beacon-uri
    # organisation variables
    BEACON_ORG_ID          = var.organisation-id
    BEACON_ORG_NAME        = var.organisation-name
    BEACON_ORG_DESCRIPTION = var.beacon-org-description
    BEACON_ORG_ADDRESS     = var.beacon-org-address
    BEACON_ORG_WELCOME_URL = var.beacon-org-welcome-url
    BEACON_ORG_CONTACT_URL = var.beacon-org-contact-url
    BEACON_ORG_LOGO_URL    = var.beacon-org-logo-url
    # beacon service variables
    BEACON_SERVICE_TYPE_GROUP    = var.beacon-service-type-group
    BEACON_SERVICE_TYPE_ARTIFACT = var.beacon-service-type-artifact
    BEACON_SERVICE_TYPE_VERSION  = var.beacon-service-type-version
    # authentication variables
    BEACON_ENABLE_AUTH = var.beacon-enable-auth
    # configurations
    CONFIG_MAX_VARIANT_SEARCH_BASE_RANGE = var.config-max-variant-search-base-range
  }
  # athena related variables
  athena_variables = {
    ATHENA_WORKGROUP               = aws_athena_workgroup.sbeacon-workgroup.name
    ATHENA_METADATA_DATABASE       = aws_glue_catalog_database.metadata-database.name
    ATHENA_METADATA_BUCKET         = aws_s3_bucket.metadata-bucket.bucket
    ATHENA_DATASETS_TABLE          = aws_glue_catalog_table.sbeacon-datasets.name
    ATHENA_DATASETS_CACHE_TABLE    = aws_glue_catalog_table.sbeacon-datasets-cache.name
    ATHENA_COHORTS_TABLE           = aws_glue_catalog_table.sbeacon-cohorts.name
    ATHENA_COHORTS_CACHE_TABLE     = aws_glue_catalog_table.sbeacon-cohorts-cache.name
    ATHENA_INDIVIDUALS_TABLE       = aws_glue_catalog_table.sbeacon-individuals.name
    ATHENA_INDIVIDUALS_CACHE_TABLE = aws_glue_catalog_table.sbeacon-individuals-cache.name
    ATHENA_BIOSAMPLES_TABLE        = aws_glue_catalog_table.sbeacon-biosamples.name
    ATHENA_BIOSAMPLES_CACHE_TABLE  = aws_glue_catalog_table.sbeacon-biosamples-cache.name
    ATHENA_RUNS_TABLE              = aws_glue_catalog_table.sbeacon-runs.name
    ATHENA_RUNS_CACHE_TABLE        = aws_glue_catalog_table.sbeacon-runs-cache.name
    ATHENA_ANALYSES_TABLE          = aws_glue_catalog_table.sbeacon-analyses.name
    ATHENA_ANALYSES_CACHE_TABLE    = aws_glue_catalog_table.sbeacon-analyses-cache.name
    ATHENA_TERMS_TABLE             = aws_cloudformation_stack.sbeacon_terms_stack.parameters.TableName
    ATHENA_TERMS_INDEX_TABLE       = aws_cloudformation_stack.sbeacon_terms_index_stack.parameters.TableName
    ATHENA_TERMS_CACHE_TABLE       = aws_glue_catalog_table.sbeacon-terms-cache.name
    ATHENA_RELATIONS_TABLE         = aws_glue_catalog_table.sbeacon-relations.name
  }
  # dynamodb variables
  dynamodb_variables = {
    DYNAMO_DATASETS_TABLE                = aws_dynamodb_table.datasets.name
    DYNAMO_VCF_SUMMARIES_TABLE           = aws_dynamodb_table.vcf_summaries.name
    DYNAMO_VARIANT_DUPLICATES_TABLE      = aws_dynamodb_table.variant_duplicates.name
    DYNAMO_VARIANT_QUERIES_TABLE         = aws_dynamodb_table.variant_queries.name
    DYNAMO_VARIANT_QUERY_RESPONSES_TABLE = aws_dynamodb_table.variant_query_responses.name
    DYNAMO_ONTOLOGIES_TABLE              = aws_dynamodb_table.ontologies.name
    DYNAMO_ANSCESTORS_TABLE              = aws_dynamodb_table.anscestor_terms.name
    DYNAMO_DESCENDANTS_TABLE             = aws_dynamodb_table.descendant_terms.name
    DYNAMO_TERM_LABELS_TABLE             = aws_dynamodb_table.term_labels.name
  }
  # layers
  binaries_layer         = "${aws_lambda_layer_version.binaries_layer.layer_arn}:${aws_lambda_layer_version.binaries_layer.version}"
  python_libraries_layer = module.python_libraries_layer.lambda_layer_arn
  python_modules_layer   = module.python_modules_layer.lambda_layer_arn
}

#
# submitDataset Lambda Function
#
module "lambda-submitDataset" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "submitDataset"
  description         = "Creates or updates a dataset and triggers summariseVcf."
  handler             = "lambda_function.lambda_handler"
  runtime             = "python3.12"
  architectures       = ["x86_64"]
  memory_size         = 1769
  timeout             = 60
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-submitDataset.json,
    data.aws_iam_policy_document.athena-full-access.json,
    data.aws_iam_policy_document.dynamodb-onto-access.json,
    data.aws_iam_policy_document.dynamodb-onto-write-access.json
  ]
  number_of_policy_jsons = 4
  source_path            = "${path.module}/lambda/submitDataset"
  tags                   = var.common-tags

  environment_variables = merge(
    {
      DYNAMO_DATASETS_TABLE = aws_dynamodb_table.datasets.name
      INDEXER_LAMBDA        = module.lambda-indexer.lambda_function_name
    },
    local.sbeacon_variables,
    local.athena_variables,
    local.dynamodb_variables
  )

  layers = [
    local.python_libraries_layer,
    local.binaries_layer,
    local.python_modules_layer
  ]
}

#
# getInfo Lambda Function
#
module "lambda-getInfo" {
  source = "terraform-aws-modules/lambda/aws"

  function_name      = "getInfo"
  description        = "Returns basic information about the beacon and the datasets."
  handler            = "lambda_function.lambda_handler"
  runtime            = "python3.12"
  memory_size        = 1769
  timeout            = 60
  attach_policy_json = true
  policy_json        = data.aws_iam_policy_document.lambda-getInfo.json
  source_path        = "${path.module}/lambda/getInfo"
  tags               = var.common-tags

  environment_variables = merge(
    local.sbeacon_variables,
    local.athena_variables,
    local.dynamodb_variables
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# getConfiguration Lambda Function
#
module "lambda-getConfiguration" {
  source = "terraform-aws-modules/lambda/aws"

  function_name      = "getConfiguration"
  description        = "Get the beacon configuration."
  runtime            = "python3.12"
  handler            = "lambda_function.lambda_handler"
  memory_size        = 1769
  timeout            = 60
  attach_policy_json = true
  policy_json        = data.aws_iam_policy_document.lambda-getConfiguration.json
  source_path        = "${path.module}/lambda/getConfiguration"

  tags = var.common-tags

  environment_variables = merge(
    local.sbeacon_variables,
    local.athena_variables,
    local.dynamodb_variables
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# getMap Lambda Function
#
module "lambda-getMap" {
  source = "terraform-aws-modules/lambda/aws"

  function_name      = "getMap"
  description        = "Get the beacon map."
  runtime            = "python3.12"
  handler            = "lambda_function.lambda_handler"
  memory_size        = 1769
  timeout            = 60
  attach_policy_json = true
  policy_json        = data.aws_iam_policy_document.lambda-getMap.json
  source_path        = "${path.module}/lambda/getMap"

  tags = var.common-tags

  environment_variables = merge(
    local.sbeacon_variables,
    local.athena_variables,
    local.dynamodb_variables
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# getEntryTypes Lambda Function
#
module "lambda-getEntryTypes" {
  source = "terraform-aws-modules/lambda/aws"

  function_name      = "getEntryTypes"
  description        = "Get the beacon map."
  runtime            = "python3.12"
  handler            = "lambda_function.lambda_handler"
  memory_size        = 1769
  timeout            = 60
  attach_policy_json = true
  policy_json        = data.aws_iam_policy_document.lambda-getEntryTypes.json
  source_path        = "${path.module}/lambda/getEntryTypes"

  tags = var.common-tags

  environment_variables = merge(
    local.sbeacon_variables,
    local.athena_variables,
    local.dynamodb_variables
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# getFilteringTerms Lambda Function
#
module "lambda-getFilteringTerms" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "getFilteringTerms"
  description         = "Get the beacon map."
  runtime             = "python3.12"
  handler             = "lambda_function.lambda_handler"
  memory_size         = 1769
  timeout             = 60
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.athena-full-access.json,
    data.aws_iam_policy_document.dynamodb-onto-access.json,
  ]
  number_of_policy_jsons = 2
  source_path            = "${path.module}/lambda/getFilteringTerms"

  tags = var.common-tags

  environment_variables = merge(
    local.sbeacon_variables,
    local.athena_variables,
    local.dynamodb_variables
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# getAnalyses Lambda Function
#
module "lambda-getAnalyses" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "getAnalyses"
  description         = "Get the beacon map."
  runtime             = "python3.12"
  handler             = "lambda_function.lambda_handler"
  memory_size         = 1769
  timeout             = 60
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-getAnalyses.json,
    data.aws_iam_policy_document.athena-full-access.json,
    data.aws_iam_policy_document.dynamodb-onto-access.json
  ]
  number_of_policy_jsons = 3
  source_path            = "${path.module}/lambda/getAnalyses"

  tags = var.common-tags

  environment_variables = merge(
    {
      SPLIT_QUERY_LAMBDA    = module.lambda-splitQuery.lambda_function_name,
      SPLIT_QUERY_TOPIC_ARN = aws_sns_topic.splitQuery.arn
    },
    local.athena_variables,
    local.sbeacon_variables,
    local.dynamodb_variables
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# getGenomicVariants Lambda Function
#
module "lambda-getGenomicVariants" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "getGenomicVariants"
  description         = "Get the variants."
  runtime             = "python3.12"
  handler             = "lambda_function.lambda_handler"
  memory_size         = 1769
  timeout             = 60
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-getGenomicVariants.json,
    data.aws_iam_policy_document.athena-full-access.json,
    data.aws_iam_policy_document.dynamodb-onto-access.json
  ]
  number_of_policy_jsons = 3
  source_path            = "${path.module}/lambda/getGenomicVariants"

  tags = var.common-tags

  environment_variables = merge(
    {
      SPLIT_QUERY_LAMBDA    = module.lambda-splitQuery.lambda_function_name,
      SPLIT_QUERY_TOPIC_ARN = aws_sns_topic.splitQuery.arn
    },
    local.athena_variables,
    local.sbeacon_variables,
    local.dynamodb_variables
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# getIndividuals Lambda Function
#
module "lambda-getIndividuals" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "getIndividuals"
  description         = "Get the individuals."
  runtime             = "python3.12"
  handler             = "lambda_function.lambda_handler"
  memory_size         = 1769
  timeout             = 60
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-getIndividuals.json,
    data.aws_iam_policy_document.athena-full-access.json,
    data.aws_iam_policy_document.dynamodb-onto-access.json
  ]
  number_of_policy_jsons = 3
  source_path            = "${path.module}/lambda/getIndividuals"

  tags = var.common-tags

  environment_variables = merge(
    {
      SPLIT_QUERY_LAMBDA    = module.lambda-splitQuery.lambda_function_name,
      SPLIT_QUERY_TOPIC_ARN = aws_sns_topic.splitQuery.arn
    },
    local.athena_variables,
    local.sbeacon_variables,
    local.dynamodb_variables
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# getBiosamples Lambda Function
#
module "lambda-getBiosamples" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "getBiosamples"
  description         = "Get the biosamples."
  runtime             = "python3.12"
  handler             = "lambda_function.lambda_handler"
  memory_size         = 1769
  timeout             = 60
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-getBiosamples.json,
    data.aws_iam_policy_document.athena-full-access.json,
    data.aws_iam_policy_document.dynamodb-onto-access.json
  ]
  number_of_policy_jsons = 3
  source_path            = "${path.module}/lambda/getBiosamples"

  tags = var.common-tags

  environment_variables = merge(
    {
      SPLIT_QUERY_LAMBDA    = module.lambda-splitQuery.lambda_function_name,
      SPLIT_QUERY_TOPIC_ARN = aws_sns_topic.splitQuery.arn
    },
    local.athena_variables,
    local.sbeacon_variables,
    local.dynamodb_variables
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# getDatasets Lambda Function
#
module "lambda-getDatasets" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "getDatasets"
  description         = "Get the datasets."
  runtime             = "python3.12"
  handler             = "lambda_function.lambda_handler"
  memory_size         = 1769
  timeout             = 60
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-getDatasets.json,
    data.aws_iam_policy_document.athena-full-access.json,
    data.aws_iam_policy_document.dynamodb-onto-access.json
  ]
  number_of_policy_jsons = 3
  source_path            = "${path.module}/lambda/getDatasets"

  tags = var.common-tags

  environment_variables = merge(
    {
      SPLIT_QUERY_LAMBDA    = module.lambda-splitQuery.lambda_function_name,
      SPLIT_QUERY_TOPIC_ARN = aws_sns_topic.splitQuery.arn
    },
    local.athena_variables,
    local.sbeacon_variables,
    local.dynamodb_variables
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# getCohorts Lambda Function
#
module "lambda-getCohorts" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "getCohorts"
  description         = "Get the cohorts."
  runtime             = "python3.12"
  handler             = "lambda_function.lambda_handler"
  memory_size         = 1769
  timeout             = 60
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-getCohorts.json,
    data.aws_iam_policy_document.athena-full-access.json,
    data.aws_iam_policy_document.dynamodb-onto-access.json
  ]
  number_of_policy_jsons = 3
  source_path            = "${path.module}/lambda/getCohorts"

  tags = var.common-tags

  environment_variables = merge(
    {
      SPLIT_QUERY_LAMBDA = module.lambda-splitQuery.lambda_function_name
    },
    local.athena_variables,
    local.sbeacon_variables,
    local.dynamodb_variables
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# getRuns Lambda Function
#
module "lambda-getRuns" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "getRuns"
  description         = "Get the runs."
  runtime             = "python3.12"
  handler             = "lambda_function.lambda_handler"
  memory_size         = 1769
  timeout             = 60
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-getRuns.json,
    data.aws_iam_policy_document.athena-full-access.json,
    data.aws_iam_policy_document.dynamodb-onto-access.json
  ]
  number_of_policy_jsons = 3
  source_path            = "${path.module}/lambda/getRuns"

  tags = var.common-tags

  environment_variables = merge(
    {
      SPLIT_QUERY_LAMBDA    = module.lambda-splitQuery.lambda_function_name,
      SPLIT_QUERY_TOPIC_ARN = aws_sns_topic.splitQuery.arn
    },
    local.athena_variables,
    local.sbeacon_variables,
    local.dynamodb_variables
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# splitQuery Lambda Function
#
module "lambda-splitQuery" {
  source = "terraform-aws-modules/lambda/aws"

  function_name      = "splitQuery"
  description        = "Splits a dataset into smaller slices of VCFs and invokes performQuery on each."
  handler            = "lambda_function.lambda_handler"
  runtime            = "python3.12"
  memory_size        = 1769
  timeout            = 30
  attach_policy_json = true
  policy_json        = data.aws_iam_policy_document.lambda-splitQuery.json
  source_path        = "${path.module}/lambda/splitQuery"
  tags               = var.common-tags

  environment_variables = {
    PERFORM_QUERY_LAMBDA    = module.lambda-performQuery.lambda_function_name,
    PERFORM_QUERY_TOPIC_ARN = aws_sns_topic.performQuery.arn
  }

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# performQuery Lambda Function
#
module "lambda-performQuery" {
  source = "terraform-aws-modules/lambda/aws"

  function_name          = "performQuery"
  description            = "Queries a slice of a vcf for a specified variant."
  handler                = "lambda_function.lambda_handler"
  runtime                = "python3.12"
  memory_size            = 1769
  timeout                = 10
  ephemeral_storage_size = 1024
  attach_policy_json     = true
  policy_json            = data.aws_iam_policy_document.lambda-performQuery.json
  source_path            = "${path.module}/lambda/performQuery"
  tags                   = var.common-tags

  layers = [
    local.binaries_layer,
    local.python_libraries_layer,
    local.python_modules_layer
  ]

  environment_variables = merge({
    VARIANTS_BUCKET = aws_s3_bucket.variants-bucket.bucket
    },
    local.sbeacon_variables,
  local.dynamodb_variables)
}

#
# indexer Lambda Function
#
module "lambda-indexer" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "indexer"
  description         = "Run the indexing tasks."
  runtime             = "python3.12"
  handler             = "lambda_function.lambda_handler"
  memory_size         = 1769
  timeout             = 600
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-indexer.json,
    data.aws_iam_policy_document.athena-full-access.json,
    data.aws_iam_policy_document.dynamodb-onto-access.json,
    data.aws_iam_policy_document.dynamodb-onto-write-access.json
  ]
  number_of_policy_jsons = 4
  source_path            = "${path.module}/lambda/indexer"

  tags = var.common-tags

  environment_variables = merge(
    local.dynamodb_variables,
    local.sbeacon_variables,
    local.athena_variables,
    { INDEXER_TOPIC_ARN : aws_sns_topic.indexer.arn }
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# admin Lambda Function
#
module "lambda-admin" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "admin"
  description         = "Run the admin tasks."
  runtime             = "python3.12"
  handler             = "lambda_function.lambda_handler"
  memory_size         = 512
  timeout             = 60
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.admin-lambda-access.json
  ]
  number_of_policy_jsons = 1
  source_path            = "${path.module}/lambda/admin"

  tags = var.common-tags

  environment_variables = merge(
    local.sbeacon_variables,
    { COGNITO_USER_POOL_ID = aws_cognito_user_pool.BeaconUserPool.id }
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# analytics Lambda Function
#
module "lambda-analytics" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "analytics"
  description         = "Run the analytics tasks."
  create_package      = false
  image_uri           = module.docker_image_analytics_lambda.image_uri
  package_type        = "Image"
  memory_size         = 512
  timeout             = 60
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.athena-full-access.json,
    data.aws_iam_policy_document.dynamodb-onto-access.json,
    data.aws_iam_policy_document.lambda-analytics.json
  ]
  number_of_policy_jsons = 3
  source_path            = "${path.module}/lambda/analytics"

  tags = var.common-tags

  environment_variables = merge(
    {
      SPLIT_QUERY_LAMBDA    = module.lambda-splitQuery.lambda_function_name,
      SPLIT_QUERY_TOPIC_ARN = aws_sns_topic.splitQuery.arn
    },
    local.athena_variables,
    local.sbeacon_variables,
    local.dynamodb_variables
  )
}

#
# askbeacon Lambda Function
#
module "lambda-askbeacon" {
  source = "terraform-aws-modules/lambda/aws"

  function_name          = "askbeacon"
  description            = "Run the llm tasks."
  create_package         = false
  image_uri              = module.docker_image_askbeacon_lambda.image_uri
  package_type           = "Image"
  memory_size            = 512
  timeout                = 60
  attach_policy_jsons    = true
  ephemeral_storage_size = 1024

  policy_jsons = [
    data.aws_iam_policy_document.s3-askbeacon-access.json,
    data.aws_iam_policy_document.athena-readonly-access.json,
    data.aws_iam_policy_document.dynamodb-onto-access.json,
  ]
  number_of_policy_jsons = 3
  source_path            = "${path.module}/lambda/askbeacon"

  tags = var.common-tags

  environment_variables = merge(
    {
      SPLIT_QUERY_LAMBDA    = module.lambda-splitQuery.lambda_function_name,
      SPLIT_QUERY_TOPIC_ARN = aws_sns_topic.splitQuery.arn
    },
    local.athena_variables,
    local.sbeacon_variables,
    local.dynamodb_variables,
    {
      AZURE_OPENAI_API_KEY              = var.azure-openai-api-key
      AZURE_OPENAI_ENDPOINT             = var.azure-openai-endpoint
      AZURE_OPENAI_API_VERSION          = var.azure-openai-api-version
      AZURE_OPENAI_CHAT_DEPLOYMENT_NAME = var.azure-openai-chat-deployment-name
      OPENAI_API_KEY                    = var.openai-api-key
      OPENAI_COMPLETIONS_MODEL_NAME     = var.openai-completions-model-name
      OPENAI_EMBEDDING_MODEL_NAME       = var.openai-embedding-model-name
      EMBEDDING_DISTANCE_THRESHOLD      = var.embedding-distance-threshold
      MPLCONFIGDIR                      = "/tmp/matplotlib-tmpdir"
    }
  )
}
