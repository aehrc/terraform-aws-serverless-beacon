resource "aws_sns_topic" "summariseDataset" {
  name = "summariseDataset"
}

resource "aws_sns_topic_subscription" "summariseDataset" {
  topic_arn = "${aws_sns_topic.summariseDataset.arn}"
  protocol = "lambda"
  endpoint = "${aws_lambda_function.summariseDataset.arn}"
}

resource "aws_sns_topic" "summariseVcf" {
  name = "summariseVcf"
}

resource "aws_sns_topic_subscription" "summariseVcf" {
  topic_arn = "${aws_sns_topic.summariseVcf.arn}"
  protocol  = "lambda"
  endpoint  = "${aws_lambda_function.summariseVcf.arn}"
}

resource "aws_sns_topic" "summariseSlice" {
  name = "summariseSlice"
}

resource "aws_sns_topic_subscription" "summariseSlice" {
  topic_arn = "${aws_sns_topic.summariseSlice.arn}"
  protocol = "lambda"
  endpoint = "${aws_lambda_function.summariseSlice.arn}"
}
