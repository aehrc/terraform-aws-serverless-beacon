resource "aws_dynamodb_table" "datasets" {
  hash_key = "id"
  name = "Datasets"
  read_capacity = 1
  write_capacity = 1

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "assemblyId"
    type = "S"
  }

  global_secondary_index {
    hash_key = "assemblyId",
    name = "assembly_index"
    non_key_attributes = [
      "vcfLocation",
      "id",
    ]
    projection_type = "INCLUDE"
    read_capacity = "4"
    write_capacity = "1"
  }
}
