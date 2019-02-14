#
# Lambda Packages
#
resource "aws_s3_bucket" "lambda-packages" {
  bucket_prefix = "beacon-api-lambda-packages"
}

resource "aws_s3_bucket_object" "submitDataset-package" {
  bucket = "${aws_s3_bucket.lambda-packages.bucket}"
  key = "submitDataset.zip"
  source = "${path.module}/lambda/submitDataset/submitDataset.zip"
  etag = "${md5(file("${path.module}/lambda/submitDataset/submitDataset.zip"))}"
}

resource "aws_s3_bucket_object" "summariseDataset-package" {
  bucket = "${aws_s3_bucket.lambda-packages.bucket}"
  key = "summariseDataset.zip"
  source = "${path.module}/lambda/summariseDataset/summariseDataset.zip"
  etag = "${md5(file("${path.module}/lambda/summariseDataset/summariseDataset.zip"))}"
}

resource "aws_s3_bucket_object" "summariseVcf-package" {
  bucket = "${aws_s3_bucket.lambda-packages.bucket}"
  key = "summariseVcf.zip"
  source = "${path.module}/lambda/summariseVcf/summariseVcf.zip"
  etag = "${md5(file("${path.module}/lambda/summariseVcf/summariseVcf.zip"))}"
}

resource "aws_s3_bucket_object" "summariseSlice-package" {
  bucket = "${aws_s3_bucket.lambda-packages.bucket}"
  key = "summariseSlice.zip"
  source = "${path.module}/lambda/summariseSlice/summariseSlice.zip"
  etag = "${md5(file("${path.module}/lambda/summariseSlice/summariseSlice.zip"))}"
}

resource "aws_s3_bucket_object" "queryDatasets-package" {
  bucket = "${aws_s3_bucket.lambda-packages.bucket}"
  key = "queryDatasets.zip"
  source = "${path.module}/lambda/queryDatasets/queryDatasets.zip"
  etag = "${md5(file("${path.module}/lambda/queryDatasets/queryDatasets.zip"))}"
}

resource "aws_s3_bucket_object" "splitQuery-package" {
  bucket = "${aws_s3_bucket.lambda-packages.bucket}"
  key = "splitQuery.zip"
  source = "${path.module}/lambda/splitQuery/splitQuery.zip"
  etag = "${md5(file("${path.module}/lambda/splitQuery/splitQuery.zip"))}"
}

resource "aws_s3_bucket_object" "performQuery-package" {
  bucket = "${aws_s3_bucket.lambda-packages.bucket}"
  key = "performQuery.zip"
  source = "${path.module}/lambda/performQuery/performQuery.zip"
  etag = "${md5(file("${path.module}/lambda/performQuery/performQuery.zip"))}"
}
