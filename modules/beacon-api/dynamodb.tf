resource "aws_dynamodb_table" "datasets" {
  hash_key = "id"
  name = "Datasets"
  read_capacity = 5
  write_capacity = 1

  attribute {
    name = "id"
    type = "S"
  }
}
