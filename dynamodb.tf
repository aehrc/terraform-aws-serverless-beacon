resource aws_dynamodb_table datasets {
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "id"
  name = "Datasets"
  tags = var.common-tags

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "assemblyId"
    type = "S"
  }

  global_secondary_index {
    hash_key = "assemblyId"
    name = "assembly_index"
    non_key_attributes = [
      "id",
      "vcfLocations",
      "vcfGroups"
    ]
    projection_type = "INCLUDE"
  }
}

resource aws_dynamodb_table vcf_summaries {
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "vcfLocation"
  name = "VcfSummaries"
  tags = var.common-tags

  attribute {
    name = "vcfLocation"
    type = "S"
  }
}

resource aws_dynamodb_table variant_duplicates {
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "contig"
  range_key = "datasetKey"
  name = "VariantDuplicates"
  tags = var.common-tags

  attribute {
    name = "contig"
    type = "S"
  }

  attribute {
    name = "datasetKey"
    type = "S"
  }
}
