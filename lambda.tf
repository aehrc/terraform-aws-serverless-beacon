#
# summariseDataset Lambda Function
#
resource "aws_lambda_permission" "SNSSummariseDataset" {
  statement_id  = "AllowSNSSummariseDatasetInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-summariseDataset.lambda_function_arn
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.summariseDataset.arn
}

#
# summariseVcf Lambda Function
#
resource "aws_lambda_permission" "SNSSummariseVcf" {
  statement_id  = "AllowSNSSummariseVcfInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-summariseVcf.lambda_function_arn
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.summariseVcf.arn
}

#
# summariseSlice Lambda Function
#
resource "aws_lambda_permission" "SNSSummariseSlice" {
  statement_id  = "AllowSNSSummariseSliceInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-summariseSlice.lambda_function_arn
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.summariseSlice.arn
}

#
# duplicateVariantSearch Lambda Function
#
resource "aws_lambda_permission" "SNSduplicateVariantSearch" {
  statement_id  = "AllowSNSduplicateVariantSearchInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-duplicateVariantSearch.lambda_function_arn
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.duplicateVariantSearch.arn
}

#
# splitQuery Lambda Function
#
resource "aws_lambda_permission" "SNSsplitQuery" {
  statement_id  = "AllowSNSsplitQueryInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-splitQuery.lambda_function_arn
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.splitQuery.arn
}


#
# performQuery Lambda Function
#
resource "aws_lambda_permission" "SNSperformQuery" {
  statement_id  = "AllowSNSperformQueryInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-performQuery.lambda_function_arn
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.performQuery.arn
}

#
# indexer Lambda Function
#
resource "aws_lambda_permission" "SNSindexer" {
  statement_id  = "AllowSNSindexerInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-indexer.lambda_function_arn
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.indexer.arn
}
