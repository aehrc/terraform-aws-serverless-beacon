resource "aws_sns_topic" "summariseDataset" {
  name = "summariseDataset"
}

resource "aws_sns_topic_subscription" "summariseDataset" {
  topic_arn = aws_sns_topic.summariseDataset.arn
  protocol  = "lambda"
  endpoint  = module.lambda-summariseDataset.lambda_function_arn
}

resource "aws_sns_topic" "summariseVcf" {
  name = "summariseVcf"
}

resource "aws_sns_topic_subscription" "summariseVcf" {
  topic_arn = aws_sns_topic.summariseVcf.arn
  protocol  = "lambda"
  endpoint  = module.lambda-summariseVcf.lambda_function_arn
}

resource "aws_sns_topic" "summariseSlice" {
  name = "summariseSlice"
}

resource "aws_sns_topic_subscription" "summariseSlice" {
  topic_arn = aws_sns_topic.summariseSlice.arn
  protocol  = "lambda"
  endpoint  = module.lambda-summariseSlice.lambda_function_arn
}

resource "aws_sns_topic" "duplicateVariantSearch" {
  name = "duplicateVariantSearch"
}

resource "aws_sns_topic_subscription" "duplicateVariantSearch" {
  topic_arn = aws_sns_topic.duplicateVariantSearch.arn
  protocol  = "lambda"
  endpoint  = module.lambda-duplicateVariantSearch.lambda_function_arn
}

resource "aws_sns_topic" "splitQuery" {
  name = "splitQuery"
}

resource "aws_sns_topic_subscription" "splitQuery" {
  topic_arn = aws_sns_topic.splitQuery.arn
  protocol  = "lambda"
  endpoint  = module.lambda-splitQuery.lambda_function_arn
}

resource "aws_sns_topic" "performQuery" {
  name = "performQuery"
}

resource "aws_sns_topic_subscription" "performQuery" {
  topic_arn = aws_sns_topic.performQuery.arn
  protocol  = "lambda"
  endpoint  = module.lambda-performQuery.lambda_function_arn
}
