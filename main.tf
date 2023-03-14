provider "aws" {
  region = var.region
}

# DOCS
# Lambda memory - https://docs.aws.amazon.com/lambda/latest/dg/configuration-function-common.html
#                 https://stackoverflow.com/questions/66522916/aws-lambda-memory-vs-cpu-configuration
#
locals {
  api_version        = "v2.0.0"
  version            = "v0.0.1"
  build_cpp_path     = abspath("${path.module}/build_cpp.sh")
  shared_source_path = abspath("${path.module}/lambda/shared/source")
  gzip_source_path   = abspath("${path.module}/lambda/shared/gzip")

  maximum_load_file_size  = 750000000
  vcf_processed_file_size = 50000000
  # TODO use the following organisation to refactor the IAM policy assignment
  # this makes the code simpler
  # sbeacon info variables
  sbeacon_variables = {
    # Beacon variables
    BEACON_API_VERSION         = local.api_version
    BEACON_ID                  = var.beacon-id
    BEACON_NAME                = var.beacon-name
    BEACON_ENVIRONMENT         = "dev"
    BEACON_DESCRIPTION         = ""
    BEACON_VERSION             = local.version
    BEACON_WELCOME_URL         = ""
    BEACON_ALTERNATIVE_URL     = ""
    BEACON_CREATE_DATETIME     = ""
    BEACON_UPDATE_DATETIME     = ""
    BEACON_HANDOVERS           = ""
    BEACON_DOCUMENTATION_URL   = ""
    BEACON_DEFAULT_GRANULARITY = "boolean"
    # Organisation variables
    BEACON_ORG_ID          = var.organisation-id
    BEACON_ORG_NAME        = var.organisation-name
    BEACON_ORG_DESCRIPTION = ""
    BEACON_ORG_ADRESS      = ""
    BEACON_ORG_WELCOME_URL = ""
    BEACON_ORG_CONTACT_URL = ""
    BEACON_ORG_LOGO_URL    = ""
    # beacon service variables
    BEACON_SERVICE_TYPE_GROUP    = ""
    BEACON_SERVICE_TYPE_ARTIFACT = ""
    BEACON_SERVICE_TYPE_VERSION  = ""
  }
  # athena related variables
  athena_variables = {
    ATHENA_WORKGROUP         = aws_athena_workgroup.sbeacon-workgroup.name
    ATHENA_METADATA_DATABASE = aws_glue_catalog_database.metadata-database.name
    ATHENA_METADATA_BUCKET   = aws_s3_bucket.metadata-bucket.bucket
    ATHENA_DATASETS_TABLE    = aws_glue_catalog_table.sbeacon-datasets.name
    ATHENA_COHORTS_TABLE     = aws_glue_catalog_table.sbeacon-cohorts.name
    ATHENA_INDIVIDUALS_TABLE = aws_glue_catalog_table.sbeacon-individuals.name
    ATHENA_BIOSAMPLES_TABLE  = aws_glue_catalog_table.sbeacon-biosamples.name
    ATHENA_RUNS_TABLE        = aws_glue_catalog_table.sbeacon-runs.name
    ATHENA_ANALYSES_TABLE    = aws_glue_catalog_table.sbeacon-analyses.name
    ATHENA_TERMS_TABLE       = aws_glue_catalog_table.sbeacon-terms.name
    ATHENA_TERMS_INDEX_TABLE = aws_glue_catalog_table.sbeacon-terms-index.name
    ATHENA_TERMS_CACHE_TABLE = aws_glue_catalog_table.sbeacon-terms-cache.name
    ATHENA_RELATIONS_TABLE   = aws_glue_catalog_table.sbeacon-relations.name
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
    DYNAMO_ONTO_INDEX_TABLE              = aws_dynamodb_table.ontology_terms.name
  }
  # layers
  binaries_layer         = "${aws_lambda_layer_version.binaries_layer.layer_arn}:${aws_lambda_layer_version.binaries_layer.version}"
  python_libraries_layer = module.python_libraries_layer.lambda_layer_arn
}

#
# submitDataset Lambda Function
#
module "lambda-submitDataset" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "submitDataset"
  description         = "Creates or updates a dataset and triggers summariseVcf."
  handler             = "lambda_function.lambda_handler"
  runtime             = "python3.9"
  architectures       = ["x86_64"]
  memory_size         = 1769
  timeout             = 60
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-submitDataset.json,
    data.aws_iam_policy_document.athena-full-access.json
  ]
  number_of_policy_jsons = 2
  source_path            = "${path.module}/lambda/submitDataset"
  tags                   = var.common-tags

  environment_variables = merge(
    {
      DYNAMO_DATASETS_TABLE           = aws_dynamodb_table.datasets.name
      SUMMARISE_DATASET_SNS_TOPIC_ARN = aws_sns_topic.summariseDataset.arn
      INDEXER_LAMBDA                  = module.lambda-indexer.lambda_function_name
    },
    local.sbeacon_variables,
    local.athena_variables,
    local.dynamodb_variables
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
  source = "terraform-aws-modules/lambda/aws"

  function_name      = "summariseDataset"
  description        = "Calculates summary counts for a dataset."
  handler            = "lambda_function.lambda_handler"
  runtime            = "python3.9"
  memory_size        = 1769
  timeout            = 60
  attach_policy_json = true
  policy_json        = data.aws_iam_policy_document.lambda-summariseDataset.json
  source_path        = "${path.module}/lambda/summariseDataset"
  tags               = var.common-tags

  environment_variables = {
    DYNAMO_DATASETS_TABLE                  = aws_dynamodb_table.datasets.name
    SUMMARISE_VCF_SNS_TOPIC_ARN            = aws_sns_topic.summariseVcf.arn
    DYNAMO_VCF_SUMMARIES_TABLE             = aws_dynamodb_table.vcf_summaries.name
    DYNAMO_VARIANT_DUPLICATES_TABLE        = aws_dynamodb_table.variant_duplicates.name
    DUPLICATE_VARIANT_SEARCH_SNS_TOPIC_ARN = aws_sns_topic.duplicateVariantSearch.arn
    VARIANTS_BUCKET                        = aws_s3_bucket.variants-bucket.bucket
    ABS_MAX_DATA_SPLIT                     = local.maximum_load_file_size
  }

  layers = [
    local.python_libraries_layer
  ]
}

#
# summariseVcf Lambda Function
#
module "lambda-summariseVcf" {
  source = "terraform-aws-modules/lambda/aws"

  function_name      = "summariseVcf"
  description        = "Calculates information in a vcf and saves it in datasets dynamoDB."
  handler            = "lambda_function.lambda_handler"
  runtime            = "python3.9"
  memory_size        = 1769
  timeout            = 60
  attach_policy_json = true
  policy_json        = data.aws_iam_policy_document.lambda-summariseVcf.json
  source_path        = "${path.module}/lambda/summariseVcf"
  tags               = var.common-tags

  environment_variables = {
    SUMMARISE_SLICE_SNS_TOPIC_ARN = aws_sns_topic.summariseSlice.arn
    VARIANTS_BUCKET               = aws_s3_bucket.variants-bucket.bucket
    DYNAMO_VCF_SUMMARIES_TABLE    = aws_dynamodb_table.vcf_summaries.name
  }

  layers = [
    local.python_libraries_layer
  ]
}

#
# summariseSlice Lambda Function
#
module "lambda-summariseSlice" {
  source = "terraform-aws-modules/lambda/aws"

  function_name      = "summariseSlice"
  description        = "Counts calls and variants in region of a vcf."
  handler            = "function"
  runtime            = "provided"
  architectures      = ["x86_64"]
  memory_size        = 1769
  timeout            = 60
  attach_policy_json = true
  policy_json        = data.aws_iam_policy_document.lambda-summariseSlice.json

  source_path = [
    {
      path = local.shared_source_path,
      commands = [
        ":zip . ./shared"
      ]
    },
    {
      path = local.gzip_source_path,
      commands = [
        ":zip . ./gzip"
      ]
    },
    {
      path = "${path.module}/lambda/summariseSlice/",
      commands = [
        "bash ${local.build_cpp_path} ./",
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
    ASSEMBLY_GSI                    = "${[for gsi in aws_dynamodb_table.datasets.global_secondary_index : gsi.name][0]}"
    DYNAMO_DATASETS_TABLE           = aws_dynamodb_table.datasets.name
    SUMMARISE_DATASET_SNS_TOPIC_ARN = aws_sns_topic.summariseDataset.arn
    SUMMARISE_SLICE_SNS_TOPIC_ARN   = aws_sns_topic.summariseSlice.arn
    DYNAMO_VCF_SUMMARIES_TABLE      = aws_dynamodb_table.vcf_summaries.name
    VARIANTS_BUCKET                 = aws_s3_bucket.variants-bucket.bucket
    MAX_SLICE_GAP                   = 100000
    VCF_S3_OUTPUT_SIZE_LIMIT        = local.vcf_processed_file_size
  }
}

#
# duplicateVariantSearch Lambda Function
#
module "lambda-duplicateVariantSearch" {
  source = "terraform-aws-modules/lambda/aws"

  function_name      = "duplicateVariantSearch"
  description        = "Searches for duplicate variants across vcfs."
  handler            = "function"
  runtime            = "provided"
  architectures      = ["x86_64"]
  memory_size        = 8192
  timeout            = 60
  attach_policy_json = true
  policy_json        = data.aws_iam_policy_document.lambda-duplicateVariantSearch.json

  source_path = [
    {
      path = local.shared_source_path,
      commands = [
        ":zip . ./shared"
      ]
    },
    {
      path = local.gzip_source_path,
      commands = [
        ":zip . ./gzip"
      ]
    },
    {
      path = "${path.module}/lambda/duplicateVariantSearch/",
      commands = [
        "bash ${local.build_cpp_path} ./",
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
    ASSEMBLY_GSI                    = "${[for gsi in aws_dynamodb_table.datasets.global_secondary_index : gsi.name][0]}"
    DYNAMO_VARIANT_DUPLICATES_TABLE = aws_dynamodb_table.variant_duplicates.name
    DYNAMO_DATASETS_TABLE           = aws_dynamodb_table.datasets.name
  }
}

#
# getInfo Lambda Function
#
module "lambda-getInfo" {
  source = "terraform-aws-modules/lambda/aws"

  function_name      = "getInfo"
  description        = "Returns basic information about the beacon and the datasets."
  handler            = "lambda_function.lambda_handler"
  runtime            = "python3.9"
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
    local.python_libraries_layer
  ]
}

#
# getConfiguration Lambda Function
#
module "lambda-getConfiguration" {
  source = "terraform-aws-modules/lambda/aws"

  function_name      = "getConfiguration"
  description        = "Get the beacon configuration."
  runtime            = "python3.9"
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
    local.python_libraries_layer
  ]
}

#
# getMap Lambda Function
#
module "lambda-getMap" {
  source = "terraform-aws-modules/lambda/aws"

  function_name      = "getMap"
  description        = "Get the beacon map."
  runtime            = "python3.9"
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
    local.python_libraries_layer
  ]
}

#
# getEntryTypes Lambda Function
#
module "lambda-getEntryTypes" {
  source = "terraform-aws-modules/lambda/aws"

  function_name      = "getEntryTypes"
  description        = "Get the beacon map."
  runtime            = "python3.9"
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
    local.python_libraries_layer
  ]
}

#
# getFilteringTerms Lambda Function
#
module "lambda-getFilteringTerms" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "getFilteringTerms"
  description         = "Get the beacon map."
  runtime             = "python3.9"
  handler             = "lambda_function.lambda_handler"
  memory_size         = 1769
  timeout             = 60
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.athena-full-access.json
  ]
  number_of_policy_jsons = 1
  source_path            = "${path.module}/lambda/getFilteringTerms"

  tags = var.common-tags

  environment_variables = merge(
    local.sbeacon_variables,
    local.athena_variables,
    local.dynamodb_variables
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

  function_name       = "getAnalyses"
  description         = "Get the beacon map."
  runtime             = "python3.9"
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
    local.python_libraries_layer
  ]
}

#
# getGenomicVariants Lambda Function
#
module "lambda-getGenomicVariants" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "getGenomicVariants"
  description         = "Get the variants."
  runtime             = "python3.9"
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
    local.python_libraries_layer
  ]
}

#
# getIndividuals Lambda Function
#
module "lambda-getIndividuals" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "getIndividuals"
  description         = "Get the individuals."
  runtime             = "python3.9"
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
    local.python_libraries_layer
  ]
}

#
# getBiosamples Lambda Function
#
module "lambda-getBiosamples" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "getBiosamples"
  description         = "Get the biosamples."
  runtime             = "python3.9"
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
    local.python_libraries_layer
  ]
}

#
# getDatasets Lambda Function
#
module "lambda-getDatasets" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "getDatasets"
  description         = "Get the datasets."
  runtime             = "python3.9"
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
    local.python_libraries_layer
  ]
}

#
# getCohorts Lambda Function
#
module "lambda-getCohorts" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "getCohorts"
  description         = "Get the cohorts."
  runtime             = "python3.9"
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
    local.python_libraries_layer
  ]
}

#
# getRuns Lambda Function
#
module "lambda-getRuns" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "getRuns"
  description         = "Get the runs."
  runtime             = "python3.9"
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
    local.python_libraries_layer
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
  runtime            = "python3.9"
  memory_size        = 1769
  timeout            = 300
  attach_policy_json = true
  policy_json        = data.aws_iam_policy_document.lambda-splitQuery.json
  source_path        = "${path.module}/lambda/splitQuery"
  tags               = var.common-tags

  environment_variables = {
    PERFORM_QUERY_LAMBDA    = module.lambda-performQuery.lambda_function_name,
    PERFORM_QUERY_TOPIC_ARN = aws_sns_topic.performQuery.arn
  }

  layers = [
    local.python_libraries_layer
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
  runtime                = "python3.9"
  memory_size            = 1769
  timeout                = 300
  ephemeral_storage_size = 1024
  attach_policy_json     = true
  policy_json            = data.aws_iam_policy_document.lambda-performQuery.json
  source_path            = "${path.module}/lambda/performQuery"
  tags                   = var.common-tags

  layers = [
    local.binaries_layer,
    local.python_libraries_layer
  ]

  environment_variables = merge({
    BEACON_API_VERSION = local.api_version
    VARIANTS_BUCKET    = aws_s3_bucket.variants-bucket.bucket
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
  runtime             = "python3.9"
  handler             = "lambda_function.lambda_handler"
  memory_size         = 1769
  timeout             = 600
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.athena-full-access.json,
    data.aws_iam_policy_document.dynamodb-onto-access.json,
    data.aws_iam_policy_document.dynamodb-onto-write-access.json
  ]
  number_of_policy_jsons = 3
  source_path            = "${path.module}/lambda/indexer"

  tags = var.common-tags

  environment_variables = merge(
    local.dynamodb_variables,
    local.sbeacon_variables,
    local.athena_variables
  )

  layers = [
    local.python_libraries_layer
  ]
}
