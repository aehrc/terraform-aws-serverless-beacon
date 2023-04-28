resource "aws_dynamodb_table" "patient_consents" {
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "vcf"
  range_key    = "sampleId"
  name         = "PatientConsents"
  tags         = var.common-tags

  attribute {
    name = "vcf"
    type = "S"
  }

  attribute {
    name = "sampleId"
    type = "S"
  }
}
