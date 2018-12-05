resource "aws_sns_topic" "updateDataset" {
  name = "updateDataset"
}

resource "aws_sns_topic_subscription" "updateDataset" {
  topic_arn = "${aws_sns_topic.updateDataset.arn}"
  protocol  = "lambda"
  endpoint  = "${aws_lambda_function.summariseVcf.arn}"
}
