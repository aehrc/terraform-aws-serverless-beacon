### jsonschema layer
# data for the python jsonschema layer
data "archive_file" "python_jsonschema_layer" {
  type        = "zip"
  source_dir = "${path.module}/layers/jsonschema/"
  output_path = "${path.module}/jsonschema.zip"
}

# python jsonschema layer definition
resource "aws_lambda_layer_version" "python_jsonschema_layer" {
  filename   = data.archive_file.python_jsonschema_layer.output_path
  layer_name = "python_jsonschema_layer"
  source_code_hash = filebase64sha256("${data.archive_file.python_jsonschema_layer.output_path}")

  compatible_runtimes = ["python3.7", "python3.8", "python3.9"]
}

### pynamodb layer
# data for the python pynamodb layer
data "archive_file" "pynamodb_layer" {
  type        = "zip"
  source_dir = "${path.module}/layers/pynamodb/"
  output_path = "${path.module}/pynamodb.zip"
}

# python pynamodb layer definition
resource "aws_lambda_layer_version" "pynamodb_layer" {
  filename   = data.archive_file.pynamodb_layer.output_path
  layer_name = "pynamodb_layer"
  source_code_hash = filebase64sha256("${data.archive_file.pynamodb_layer.output_path}")

  compatible_runtimes = ["python3.7", "python3.8", "python3.9"]
}

### jsonschema layer
# data for the python jsonschema layer
data "archive_file" "binaries_layer" {
  type        = "zip"
  source_dir = "${path.module}/layers/binaries/"
  output_path = "${path.module}/binaries.zip"
}

# python jsonschema layer definition
resource "aws_lambda_layer_version" "binaries_layer" {
  filename   = data.archive_file.binaries_layer.output_path
  layer_name = "binaries_layer"
  source_code_hash = filebase64sha256("${data.archive_file.binaries_layer.output_path}")

  compatible_runtimes = ["python3.7", "python3.8", "python3.9"]
}

### jsons layer
# data for the python jsonschema layer
data "archive_file" "python_jsons_layer" {
  type        = "zip"
  source_dir = "${path.module}/layers/jsons/"
  output_path = "${path.module}/python_jsons.zip"
}

# python jsonschema layer definition
resource "aws_lambda_layer_version" "python_jsons_layer" {
  filename   = data.archive_file.python_jsons_layer.output_path
  layer_name = "python_jsons_layer"
  source_code_hash = filebase64sha256("${data.archive_file.python_jsons_layer.output_path}")

  compatible_runtimes = ["python3.7", "python3.8", "python3.9"]
}
