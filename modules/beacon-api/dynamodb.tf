resource "aws_dynamodb_table" "datasets" {
  hash_key = "id"
  name = "Datasets"
  read_capacity = 5
  write_capacity = 1

  attribute {
    name = "id"
    type = "S"
  }

  global_secondary_index {
    hash_key = "assemblyId",
    name = "assembly_index"
    non_key_attributes = [
      "vcfLocation",
    ]
    projection_type = "INCLUDE"
    range_key = "assemblyId"
  }
}
