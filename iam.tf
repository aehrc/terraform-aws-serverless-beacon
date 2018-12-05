#
# Generic policy documents
#
data "aws_iam_policy_document" "main-lambda" {
  statement {
    actions = [
      "sts:AssumeRole",
    ]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "main-apigateway" {
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
resource "aws_iam_role" "lambda-submitDataset" {
  name = "submitDatasetLamdaRole"
  assume_role_policy = "${data.aws_iam_policy_document.main-lambda.json}"
}

resource "aws_iam_role_policy_attachment" "lambda-submitDataset-xray-write" {
  role = "${aws_iam_role.lambda-submitDataset.name}"
  policy_arn = "arn:aws:iam::aws:policy/AWSXrayWriteOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "lambda-submitDataset-add-logs" {
  role = "${aws_iam_role.lambda-submitDataset.name}"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda-submitDataset" {
  role = "${aws_iam_role.lambda-submitDataset.name}"
  policy_arn = "${aws_iam_policy.lambda-submitDataset.arn}"
}

resource "aws_iam_policy" "lambda-submitDataset" {
  name_prefix = "submitDataset"
  policy = "${data.aws_iam_policy_document.lambda-submitDataset.json}"
}

data "aws_iam_policy_document" "lambda-submitDataset" {
  statement {
    actions = [
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
    ]
    resources = [
      "${aws_dynamodb_table.datasets.arn}",
    ]
  }

  statement {
    actions = [
      "SNS:Publish",
    ]
    resources = [
      "${aws_sns_topic.updateDataset.arn}",
    ]
  }
}

#
# summariseVcf Lambda Function
#
resource "aws_iam_role" "lambda-summariseVcf" {
  name = "summariseVcfLamdaRole"
  assume_role_policy = "${data.aws_iam_policy_document.main-lambda.json}"
}

resource "aws_iam_role_policy_attachment" "lambda-summariseVcf-xray-write" {
  role = "${aws_iam_role.lambda-summariseVcf.name}"
  policy_arn = "arn:aws:iam::aws:policy/AWSXrayWriteOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "lambda-summariseVcf-add-logs" {
  role = "${aws_iam_role.lambda-summariseVcf.name}"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda-summariseVcf" {
  role = "${aws_iam_role.lambda-summariseVcf.name}"
  policy_arn = "${aws_iam_policy.lambda-summariseVcf.arn}"
}

resource "aws_iam_policy" "lambda-summariseVcf" {
  name_prefix = "summariseVcf"
  policy = "${data.aws_iam_policy_document.lambda-summariseVcf.json}"
}

data "aws_iam_policy_document" "lambda-summariseVcf" {
  statement {
    actions = [
      "dynamodb:UpdateItem",
    ]
    resources = [
      "${aws_dynamodb_table.datasets.arn}",
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
# queryDatasets Lambda Function
#
resource "aws_iam_role" "lambda-queryDatasets" {
  name = "queryDatasetsLamdaRole"
  assume_role_policy = "${data.aws_iam_policy_document.main-lambda.json}"
}

resource "aws_iam_role_policy_attachment" "lambda-queryDatasets-xray-write" {
  role = "${aws_iam_role.lambda-queryDatasets.name}"
  policy_arn = "arn:aws:iam::aws:policy/AWSXrayWriteOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "lambda-queryDatasets-add-logs" {
  role = "${aws_iam_role.lambda-queryDatasets.name}"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda-queryDatasets" {
  role = "${aws_iam_role.lambda-queryDatasets.name}"
  policy_arn = "${aws_iam_policy.lambda-queryDatasets.arn}"
}

resource "aws_iam_policy" "lambda-queryDatasets" {
  name_prefix = "queryDatasets"
  policy = "${data.aws_iam_policy_document.lambda-queryDatasets.json}"
}

data "aws_iam_policy_document" "lambda-queryDatasets" {
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
    resources = ["${aws_lambda_function.performQuery.arn}"]
  }
}

#
# performQuery Lambda Function
#
resource "aws_iam_role" "lambda-performQuery" {
  name = "performQueryLamdaRole"
  assume_role_policy = "${data.aws_iam_policy_document.main-lambda.json}"
}

resource "aws_iam_role_policy_attachment" "lambda-performQuery-xray-write" {
  role = "${aws_iam_role.lambda-performQuery.name}"
  policy_arn = "arn:aws:iam::aws:policy/AWSXrayWriteOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "lambda-performQuery-add-logs" {
  role = "${aws_iam_role.lambda-performQuery.name}"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda-performQuery" {
  role = "${aws_iam_role.lambda-performQuery.name}"
  policy_arn = "${aws_iam_policy.lambda-performQuery.arn}"
}

resource "aws_iam_policy" "lambda-performQuery" {
  name_prefix = "performQuery"
  policy = "${data.aws_iam_policy_document.lambda-performQuery.json}"
}

data "aws_iam_policy_document" "lambda-performQuery" {
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
resource "aws_iam_role" "api-root-get" {
  name = "apiRootGetRole"
  assume_role_policy = "${data.aws_iam_policy_document.main-apigateway.json}"
}

resource "aws_iam_role_policy_attachment" "api-root-get" {
  role = "${aws_iam_role.api-root-get.name}"
  policy_arn = "${aws_iam_policy.api-root-get.arn}"
}

resource "aws_iam_policy" "api-root-get" {
  name_prefix = "api-root-get"
  policy = "${data.aws_iam_policy_document.api-root-get.json}"
}

data "aws_iam_policy_document" "api-root-get" {
  statement {
    actions = [
      "dynamodb:Scan",
    ]
    resources = [
      "${aws_dynamodb_table.datasets.arn}",
    ]
  }
}

