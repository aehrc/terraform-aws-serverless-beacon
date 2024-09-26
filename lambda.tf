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
