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
  hash_key     = "prefix"
  tags         = var.common-tags

  attribute {
    name = "prefix"
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

# ontology term index
resource "aws_dynamodb_table" "ontology_terms" {
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  name         = "OntoIndex"
  tags         = var.common-tags

  # this is the tab concatenated value of
  # tableName, columnName, term
  # this must not be repeated
  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "tableName"
    type = "S"
  }

  attribute {
    name = "tableTerms"
    type = "S"
  }

  attribute {
    name = "term"
    type = "S"
  }

  # be able to query a term
  global_secondary_index {
    hash_key        = "term"
    name            = "term_index"
    projection_type = "ALL"
  }

  # be able to query a tableName
  global_secondary_index {
    hash_key        = "tableName"
    name            = "table_index"
    projection_type = "ALL"
  }

  # be able to query a terms in a table
  # tab concatenated value of table and term
  global_secondary_index {
    hash_key        = "tableTerms"
    name            = "tableterms_index"
    projection_type = "ALL"
  }
}