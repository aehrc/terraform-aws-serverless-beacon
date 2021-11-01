#
# S3 bucket for persisted vcf summaries (duplicate variant search feature)
#
resource "aws_s3_bucket" "s3-summaries-bucket" {
  bucket_prefix = var.summaries-bucket-prefix
  acl = "private"
  tags = var.common-tags
}
