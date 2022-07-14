#
# S3 bucket for persisted vcf summaries (duplicate variant search feature)
#
resource "aws_s3_bucket" "variants-bucket" {
  bucket_prefix = var.variants-bucket-prefix
  force_destroy = true
  tags = var.common-tags
}

resource "aws_s3_bucket_acl" "variants_bucket_acl" {
  bucket = aws_s3_bucket.variants-bucket.id
  acl    = "private"
}
