locals {
  udf_source_directory = "${path.module}/lambda/udfs/src/"

  udf_source_directory_files = fileset(local.udf_source_directory, "**")
  udf_source_file_hashes = {
    for path in local.udf_source_directory_files :
    path => filebase64sha512("${local.udf_source_directory}/${path}")
  }
  udf_overall_hash = base64sha512(jsonencode(local.udf_source_file_hashes))
}

resource "null_resource" "udf_compile" {
  triggers = {
    fileshash = local.udf_overall_hash
  }

  provisioner "local-exec" {
    command = "cd ${path.module}/lambda/udfs && mvn clean install -Dpublishing=true -DskipTests -s ../../mvn-settings.xml"
  }
}

#
# UDF test
#
module "lambda-udf" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "udf-test-tf"
  description   = ""
  handler       = "com.amazonaws.athena.connectors.udfs.AthenaUDFHandler"
  runtime       = "java11"
  architectures = ["x86_64"]
  memory_size   = 3008
  timeout       = 900

  create_package         = false
  local_existing_package = "${path.module}/lambda/udfs/target/athena-udfs-2022.39.1.jar"
  hash_extra             = local.udf_overall_hash
  depends_on             = [null_resource.udf_compile]

  tags = var.common-tags
}
