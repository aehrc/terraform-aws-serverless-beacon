resource "aws_dynamodb_table" "datasets" {
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  name         = "Datasets"
  tags         = var.common-tags

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
    name     = "assembly_index"
    non_key_attributes = [
      "id",
      "vcfLocations",
      "vcfGroups",
      "vcfChromosomeMap"
    ]
    projection_type = "INCLUDE"
  }
}

resource "aws_dynamodb_table" "ontologies" {
  billing_mode = "PAY_PER_REQUEST"
  name         = "Ontologies"
  hash_key     = "id"
  tags         = var.common-tags

  attribute {
    name = "id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "term_labels" {
  billing_mode = "PAY_PER_REQUEST"
  name         = "TermLabels"
  hash_key     = "term"
  tags         = var.common-tags

  attribute {
    name = "term"
    type = "S"
  }
}

resource "aws_dynamodb_table" "descendant_terms" {
  billing_mode = "PAY_PER_REQUEST"
  name         = "Descendants"
  hash_key     = "term"
  tags         = var.common-tags

  attribute {
    name = "term"
    type = "S"
  }
}

resource "aws_dynamodb_table" "anscestor_terms" {
  billing_mode = "PAY_PER_REQUEST"
  name         = "Anscestors"
  hash_key     = "term"
  tags         = var.common-tags

  attribute {
    name = "term"
    type = "S"
  }
}

resource "aws_dynamodb_table" "vcf_summaries" {
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "vcfLocation"
  name         = "VcfSummaries"
  tags         = var.common-tags

  attribute {
    name = "vcfLocation"
    type = "S"
  }
}

resource "aws_dynamodb_table" "variant_duplicates" {
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "contig"
  range_key    = "datasetKey"
  name         = "VariantDuplicates"
  tags         = var.common-tags

  attribute {
    name = "contig"
    type = "S"
  }

  attribute {
    name = "datasetKey"
    type = "S"
  }
}

# this table holds the query made by user
# this is used to control the lambdas that
# execute a given query
# resonses counts the completed lambdas
resource "aws_dynamodb_table" "variant_queries" {
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  name         = "VariantQueries"
  tags         = var.common-tags

  attribute {
    name = "id"
    type = "S"
  }

  # enable this later to save cost
  ttl {
    attribute_name = "timeToExist"
    enabled        = true
  }
}

# this table holds responses by perform query operation
# responseIndex is used to order and paginate
# this points to a JSON files with results
resource "aws_dynamodb_table" "variant_query_responses" {
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  range_key    = "responseNumber"
  name         = "VariantQueryResponses"
  tags         = var.common-tags

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "responseNumber"
    type = "N"
  }

  local_secondary_index {
    range_key       = "responseNumber"
    name            = "responseNumber_index"
    projection_type = "ALL"
  }

  # enable this later to save cost
  ttl {
    attribute_name = "timeToExist"
    enabled        = true
  }
}
