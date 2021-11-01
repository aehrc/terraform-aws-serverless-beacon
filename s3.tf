#
# S3 bucket for persisted vcf summaries (duplicate variant search feature)
#
resource "aws_s3_bucket" "variants-bucket" {
  bucket_prefix = var.variants-bucket-prefix
  acl = "private"
  tags = var.common-tags
}
