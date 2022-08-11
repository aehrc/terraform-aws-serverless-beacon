#
# Generic policy documents
#
data aws_iam_policy_document main-apigateway {
  statement {
    actions = [
      "sts:AssumeRole",
    ]
    principals {
      type        = "Service"
      identifiers = ["apigateway.amazonaws.com"]
    }
  }
}

#
# submitDataset Lambda Function
#
data aws_iam_policy_document lambda-submitDataset {
  statement {
    actions = [
      "dynamodb:DescribeTable",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:GetItem",
    ]
    resources = [
      aws_dynamodb_table.datasets.arn,
    ]
  }

  statement {
    actions = [
      "SNS:Publish",
    ]
    resources = [
      aws_sns_topic.summariseDataset.arn,
    ]
  }

  statement {
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = ["*"]
  }
}

#
#
# summariseDataset Lambda Function
#
data aws_iam_policy_document lambda-summariseDataset {
  statement {
    actions = [
      "dynamodb:UpdateItem",
      "dynamodb:Query",
    ]
    resources = [
      aws_dynamodb_table.datasets.arn,
      aws_dynamodb_table.variant_duplicates.arn,
    ]
  }

  statement {
    actions = [
      "dynamodb:BatchGetItem",
    ]
    resources = [
      aws_dynamodb_table.vcf_summaries.arn,
    ]
  }

  statement {
    actions = [
      "SNS:Publish",
    ]
    resources = [
      aws_sns_topic.summariseVcf.arn,
      aws_sns_topic.duplicateVariantSearch.arn,
    ]
  }

  statement {
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = ["*"]
  }
}

#
# summariseVcf Lambda Function
#
data aws_iam_policy_document lambda-summariseVcf {
  statement {
    actions = [
      "dynamodb:UpdateItem",
    ]
    resources = [
      aws_dynamodb_table.vcf_summaries.arn,
    ]
  }

  statement {
    actions = [
      "SNS:Publish",
    ]
    resources = [
      aws_sns_topic.summariseSlice.arn,
    ]
  }

  statement {
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = ["*"]
  }

  statement {
    actions = [
      "s3:DeleteObject",
    ]
    resources = [
      "${aws_s3_bucket.variants-bucket.arn}/*"
    ]
  }
}

#
# summariseSlice Lambda Function
#
data aws_iam_policy_document lambda-summariseSlice {
  statement {
    actions = [
      "dynamodb:UpdateItem",
    ]
    resources = [
      aws_dynamodb_table.datasets.arn,
      aws_dynamodb_table.vcf_summaries.arn,
    ]
  }

  statement {
    actions = [
      "SNS:Publish",
    ]
    resources = [
      aws_sns_topic.summariseDataset.arn,
      aws_sns_topic.summariseSlice.arn,
      aws_sns_topic.duplicateVariantSearch.arn
    ]
  }

  statement {
    actions = [
      "dynamodb:Scan",
    ]
    resources = [
      aws_dynamodb_table.datasets.arn,
      "${aws_dynamodb_table.datasets.arn}/index/*",
    ]
  }

  statement {
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
      "s3:PutObject",
    ]
    resources = ["*"]
  }
}

#
# duplicateVariantSearch Lambda Function
#
data aws_iam_policy_document lambda-duplicateVariantSearch {
  statement {
    actions = [
      "dynamodb:UpdateItem",
    ]
    resources = [
      aws_dynamodb_table.variant_duplicates.arn,
      aws_dynamodb_table.datasets.arn,
    ]
  }

  statement {
    actions = [
      "SNS:Publish",
    ]
    resources = [
      aws_sns_topic.summariseDataset.arn,
      aws_sns_topic.duplicateVariantSearch.arn,
    ]
  }

  statement {
    actions = [
      "dynamodb:Scan",
    ]
    resources = [
      aws_dynamodb_table.datasets.arn,
      "${aws_dynamodb_table.datasets.arn}/index/*",
    ]
  }

  statement {
    actions = [
      "s3:GetObject",
      "s3:PutObject",
    ]
    resources = ["*"]
  }
}

#
# getInfo Lambda Function
#
data aws_iam_policy_document lambda-getInfo {
  statement {
    actions = [
      "dynamodb:Scan",
    ]
    resources = [
      aws_dynamodb_table.datasets.arn,
    ]
  }
}

#
# getConfiguration Lambda Function
#
data aws_iam_policy_document lambda-getConfiguration {
  statement {
    actions = [
      "dynamodb:Scan",
    ]
    resources = [
      aws_dynamodb_table.datasets.arn,
    ]
  }
}

#
# getMap Lambda Function
#
data aws_iam_policy_document lambda-getMap {
  statement {
    actions = [
      "dynamodb:Scan",
    ]
    resources = [
      aws_dynamodb_table.datasets.arn,
    ]
  }
}

#
# getEntryTypes Lambda Function
#
data aws_iam_policy_document lambda-getEntryTypes {
  statement {
    actions = [
      "dynamodb:Scan",
    ]
    resources = [
      aws_dynamodb_table.datasets.arn,
    ]
  }
}

#
# getFilteringTerms Lambda Function
#
data aws_iam_policy_document lambda-getFilteringTerms {
  statement {
    actions = [
      "dynamodb:Scan",
    ]
    resources = [
      aws_dynamodb_table.datasets.arn,
    ]
  }

  statement {
    actions = [
      "athena:GetQueryExecution",
      "athena:GetQueryResults",
      "athena:StartQueryExecution"
    ]
    resources = [
      aws_athena_workgroup.sbeacon-workgroup.arn,
    ]
  }

  statement {
    actions = [
      "glue:*"
    ]
    resources = [
      "*"
    ]
  }

  statement {
    actions = [
      "s3:*",
    ]
    resources = [
      "arn:aws:s3:::${aws_s3_bucket.metadata-bucket.bucket}",
      "arn:aws:s3:::${aws_s3_bucket.metadata-bucket.bucket}/*"
    ]
  }
}

#
# getAnalyses Lambda Function
#
data aws_iam_policy_document lambda-getAnalyses {
  statement {
    actions = [
      "dynamodb:Scan",
    ]
    resources = [
      aws_dynamodb_table.datasets.arn,
    ]
  }
}

#
# getGenomicVariants Lambda Function
#
data aws_iam_policy_document lambda-getGenomicVariants {
  statement {
    actions = [
      "dynamodb:Query",
    ]
    resources = [
      "${aws_dynamodb_table.datasets.arn}/index/*",
      "${aws_dynamodb_table.variant_query_responses.arn}/index/*",
    ]
  }

  statement {
    actions = [
      "dynamodb:DescribeTable",
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
    ]
    resources = [
      aws_dynamodb_table.datasets.arn,
      aws_dynamodb_table.variant_queries.arn,
      aws_dynamodb_table.variant_query_responses.arn,
    ]
  }

  statement {
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = ["*"]
  }

  statement {
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [module.lambda-splitQuery.function_arn]
  }

  statement {
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [module.lambda-performQuery.function_arn]
  }

  statement {
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = ["*"]
  }
}

#
# queryDatasets Lambda Function
#
data aws_iam_policy_document lambda-queryDatasets {
  statement {
    actions = [
      "dynamodb:Query",
    ]
    resources = [
      "${aws_dynamodb_table.datasets.arn}/index/*",
    ]
  }

  statement {
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [module.lambda-splitQuery.function_arn]
  }

  statement {
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = ["*"]
  }
}

#
# splitQuery Lambda Function
#
data aws_iam_policy_document lambda-splitQuery {
  statement {
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [module.lambda-performQuery.function_arn]
  }
}

#
# performQuery Lambda Function
#
data aws_iam_policy_document lambda-performQuery {
  statement {
    actions = [
      "dynamodb:DescribeTable",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:GetItem",
    ]
    resources = [
      aws_dynamodb_table.datasets.arn,
      aws_dynamodb_table.variant_queries.arn,
      aws_dynamodb_table.variant_query_responses.arn,
    ]
  }

  statement {
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket",
    ]
    resources = ["*"]
  }
}
