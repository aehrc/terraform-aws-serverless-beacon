#
# Lambda Packages
#
resource "aws_s3_bucket" "lambda-packages" {
  bucket_prefix = "beacon-api-lambda-packages"
}

resource "aws_s3_bucket_object" "summariseVcf-package" {
  bucket = "${aws_s3_bucket.lambda-packages.bucket}"
  key = "summariseVcf.zip"
  source = "/tmp/lambda-summariseVcf.zip"
  etag = "${md5(file("/tmp/lambda-summariseVcf.zip"))}"
}

resource "aws_s3_bucket_object" "queryDatasets-package" {
  bucket = "${aws_s3_bucket.lambda-packages.bucket}"
  key = "queryDatasets.zip"
  source = "/tmp/lambda-queryDatasets.zip"
  etag = "${md5(file("/tmp/lambda-queryDatasets.zip"))}"
}

resource "aws_s3_bucket_object" "performQuery-package" {
  bucket = "${aws_s3_bucket.lambda-packages.bucket}"
  key = "performQuery.zip"
  source = "/tmp/lambda-performQuery.zip"
  etag = "${md5(file("/tmp/lambda-performQuery.zip"))}"
}
