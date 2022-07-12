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
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
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
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = ["*"]
  }
}

#
# API: / GET
#
resource aws_iam_role api-root-get {
  name = "apiRootGetRole"
  assume_role_policy = data.aws_iam_policy_document.main-apigateway.json
  tags = var.common-tags
}

resource aws_iam_role_policy_attachment api-root-get {
  role = aws_iam_role.api-root-get.name
  policy_arn = aws_iam_policy.api-root-get.arn
}

resource aws_iam_policy api-root-get {
  name_prefix = "api-root-get"
  policy = data.aws_iam_policy_document.api-root-get.json
}

data aws_iam_policy_document api-root-get {
  statement {
    actions = [
      "dynamodb:Scan",
    ]
    resources = [
      aws_dynamodb_table.datasets.arn,
    ]
  }
}
