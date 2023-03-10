#
# S3 bucket for persisted vcf summaries and variant queries
#
resource "aws_s3_bucket" "variants-bucket" {
  bucket_prefix = var.variants-bucket-prefix
  force_destroy = true
  tags          = var.common-tags
}

resource "aws_s3_bucket_acl" "variants_bucket_acl" {
  bucket = aws_s3_bucket.variants-bucket.id
  acl    = "private"
}

resource "aws_s3_bucket_lifecycle_configuration" "variants_bucket_lifecycle" {
  bucket = aws_s3_bucket.variants-bucket.id

  rule {
    id     = "clean-old-queries"
    status = "Enabled"

    filter {
      prefix = "variant-queries/"
    }

    expiration {
      days = 1
    }
  }
}

# 
# S3 bucket for metadata handling
# 
resource "aws_s3_bucket" "metadata-bucket" {
  bucket_prefix = var.metadata-bucket-prefix
  force_destroy = true
  tags          = var.common-tags
}

resource "aws_s3_bucket_acl" "metadata" {
  bucket = aws_s3_bucket.metadata-bucket.id
  acl    = "private"
}

resource "aws_s3_bucket_lifecycle_configuration" "metadata_bucket_lifecycle" {
  bucket = aws_s3_bucket.metadata-bucket.id

  rule {
    id     = "clean-old-query-results"
    status = "Enabled"

    filter {
      prefix = "query-results/"
    }

    expiration {
      days = 2
    }
  }

  rule {
    id     = "clean-old-cached-results"
    status = "Enabled"

    filter {
      prefix = "query-responses/"
    }

    expiration {
      days = 2
    }
  }
}

# 
# S3 bucket for lambda layers
# 
resource "aws_s3_bucket" "lambda-layers-bucket" {
  bucket_prefix = var.lambda-layers-bucket-prefix
  force_destroy = true
  tags          = var.common-tags
}

resource "aws_s3_bucket_acl" "lambda-layers" {
  bucket = aws_s3_bucket.lambda-layers-bucket.id
  acl    = "private"
}
