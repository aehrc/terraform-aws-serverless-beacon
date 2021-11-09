locals {
  api_version = "v1.0.0"
  build_cpp_path = abspath("${path.module}/build_cpp.sh")
  build_share_path = abspath("${path.module}/lambda/shared/source")
  build_gzip_path = abspath("${path.module}/lambda/shared/gzip")

  maximum_load_file_size  = 100000000
  vcf_processed_file_size = 5000
}

#
# submitDataset Lambda Function
#
module "lambda-submitDataset" {
  source = "github.com/bhosking/terraform-aws-lambda"

  function_name = "submitDataset"
  description = "Creates or updates a dataset and triggers summariseVcf."
  handler = "lambda_function.lambda_handler"
  runtime = "python3.6"
  memory_size = 2048
  timeout = 60
  policy = {
    json = data.aws_iam_policy_document.lambda-submitDataset.json
  }
  source_path = "${path.module}/lambda/submitDataset"
  tags = var.common-tags

  environment = {
    variables = {
      DATASETS_TABLE = aws_dynamodb_table.datasets.name
      SUMMARISE_DATASET_SNS_TOPIC_ARN = aws_sns_topic.summariseDataset.arn
    }
  }
}

#
# summariseDataset Lambda Function
#
module "lambda-summariseDataset" {
  source = "github.com/bhosking/terraform-aws-lambda"

  function_name = "summariseDataset"
  description = "Calculates summary counts for a dataset."
  handler = "lambda_function.lambda_handler"
  runtime = "python3.7"
  memory_size = 2048
  timeout = 60
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
  memory_size = 2048
  timeout = 60
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
  memory_size = 768
  timeout = 60
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
  memory_size = 1536
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

#
# getInfo Lambda Function
#
module "lambda-getInfo" {
  source = "github.com/bhosking/terraform-aws-lambda"

  function_name = "getInfo"
  description = "Returns basic information about the beacon and the datasets."
  handler = "lambda_function.lambda_handler"
  runtime = "python3.6"
  memory_size = 2048
  timeout = 28
  policy = {
    json = data.aws_iam_policy_document.lambda-getInfo.json
  }
  source_path = "${path.module}/lambda/getInfo"
  tags = var.common-tags

  environment = {
    variables = {
      BEACON_API_VERSION = local.api_version
      BEACON_ID = var.beacon-id
      BEACON_NAME = var.beacon-name
      DATASETS_TABLE = aws_dynamodb_table.datasets.name
      ORGANISATION_ID = var.organisation-id
      ORGANISATION_NAME = var.organisation-name
    }
  }
}

#
# queryDatasets Lambda Function
#
module "lambda-queryDatasets" {
  source = "github.com/bhosking/terraform-aws-lambda"

  function_name = "queryDatasets"
  description = "Invokes splitQuery for each dataset and returns result."
  handler = "lambda_function.lambda_handler"
  runtime = "python3.6"
  memory_size = 2048
  timeout = 28
  policy = {
    json = data.aws_iam_policy_document.lambda-queryDatasets.json
  }
  source_path = "${path.module}/lambda/queryDatasets"
  tags = var.common-tags

  environment = {
    variables = {
      BEACON_ID = var.beacon-id
      DATASETS_TABLE = aws_dynamodb_table.datasets.name
      SPLIT_QUERY_LAMBDA = module.lambda-splitQuery.function_name
    }
  }
}

#
# splitQuery Lambda Function
#
module "lambda-splitQuery" {
  source = "github.com/bhosking/terraform-aws-lambda"

  function_name = "splitQuery"
  description = "Splits a dataset into smaller slices of VCFs and invokes performQuery on each."
  handler = "lambda_function.lambda_handler"
  runtime = "python3.6"
  memory_size = 2048
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
}

#
# performQuery Lambda Function
#
module "lambda-performQuery" {
  source = "github.com/bhosking/terraform-aws-lambda"

  function_name = "performQuery"
  description = "Queries a slice of a vcf for a specified variant."
  handler = "lambda_function.lambda_handler"
  runtime = "python3.6"
  memory_size = 2048
  timeout = 24
  policy = {
    json = data.aws_iam_policy_document.lambda-performQuery.json
  }
  source_path = "${path.module}/lambda/performQuery"
  tags = var.common-tags
}
