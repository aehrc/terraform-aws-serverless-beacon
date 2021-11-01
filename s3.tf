#
# S3 bucket for persisted vcf summaries (duplicate variant search feature)
#
resource "aws_s3_bucket" "variants-bucket" {
  bucket_prefix = var.variants-bucket-prefix
  acl = "private"
  force_destroy = true
  tags = var.common-tags
}
