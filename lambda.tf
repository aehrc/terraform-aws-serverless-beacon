#
# submitDataset Lambda Function
#
resource aws_lambda_permission APISubmitDataset {
  statement_id = "AllowAPISubmitDatasetInvoke"
  action = "lambda:InvokeFunction"
  function_name = module.lambda-submitDataset.lambda_function_arn
  principal = "apigateway.amazonaws.com"
  source_arn = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.submit.path_part}"
}

#
# summariseDataset Lambda Function
#
resource aws_lambda_permission SNSSummariseDataset {
  statement_id = "AllowSNSSummariseDatasetInvoke"
  action = "lambda:InvokeFunction"
  function_name = module.lambda-summariseDataset.lambda_function_arn
  principal = "sns.amazonaws.com"
  source_arn = aws_sns_topic.summariseDataset.arn
}

#
# summariseVcf Lambda Function
#
resource aws_lambda_permission SNSSummariseVcf {
  statement_id = "AllowSNSSummariseVcfInvoke"
  action = "lambda:InvokeFunction"
  function_name = module.lambda-summariseVcf.lambda_function_arn
  principal = "sns.amazonaws.com"
  source_arn = aws_sns_topic.summariseVcf.arn
}

#
# summariseSlice Lambda Function
#
resource aws_lambda_permission SNSSummariseSlice {
  statement_id = "AllowSNSSummariseSliceInvoke"
  action = "lambda:InvokeFunction"
  function_name = module.lambda-summariseSlice.lambda_function_arn
  principal = "sns.amazonaws.com"
  source_arn = aws_sns_topic.summariseSlice.arn
}

#
# duplicateVariantSearch Lambda Function
#
resource aws_lambda_permission SNSduplicateVariantSearch {
  statement_id = "AllowSNSduplicateVariantSearchInvoke"
  action = "lambda:InvokeFunction"
  function_name = module.lambda-duplicateVariantSearch.lambda_function_arn
  principal = "sns.amazonaws.com"
  source_arn = aws_sns_topic.duplicateVariantSearch.arn
}

