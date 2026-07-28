# 
# Metadata tables on AWS Athena
# AWS docs to refer;
# SerDe types from https://docs.aws.amazon.com/athena/latest/ug/athena-ug.pdf
# Glue docs; https://docs.aws.amazon.com/glue/latest/dg/glue-dg.pdf
# Athena does not support - in database names, use _ instead
#
resource "aws_glue_catalog_database" "metadata-database" {
  name = "sbeacon_metadata"
}

# 
# SNPs metadata
#
resource "aws_glue_catalog_table" "sbeacon-snps" {
  name          = "sbeacon_snps"
  database_name = aws_glue_catalog_database.metadata-database.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    "orc.compress" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.metadata-bucket.bucket}/snps"
    input_format  = "org.apache.hadoop.hive.ql.io.orc.OrcInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.orc.OrcOutputFormat"


    ser_de_info {
      name                  = "ORC"
      serialization_library = "org.apache.hadoop.hive.ql.io.orc.OrcSerde"

      parameters = {
        "serialization.format"      = 1,
        "orc.column.index.access"   = "FALSE"
        "hive.orc.use-column-names" = "TRUE"
      }
    }

    columns {
      name = "dataset_id"
      type = "string"
    }


    columns {
      name = "id"
      type = "string"
    }

    columns {
      name = "chromosome"
      type = "string"
    }

    columns {
      name = "coordinate"
      type = "double"
    }

    columns {
      name = "allelea_top_base"
      type = "string"
    }

    columns {
      name = "alleleb_top_base"
      type = "string"
    }
  }
}

# 
# Samples metadata
#
resource "aws_glue_catalog_table" "sbeacon-samples" {
  name          = "sbeacon_samples"
  database_name = aws_glue_catalog_database.metadata-database.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    "orc.compress" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.metadata-bucket.bucket}/samples"
    input_format  = "org.apache.hadoop.hive.ql.io.orc.OrcInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.orc.OrcOutputFormat"


    ser_de_info {
      name                  = "ORC"
      serialization_library = "org.apache.hadoop.hive.ql.io.orc.OrcSerde"

      parameters = {
        "serialization.format"      = 1,
        "orc.column.index.access"   = "FALSE"
        "hive.orc.use-column-names" = "TRUE"
      }
    }

    columns {
      name = "dataset_id"
      type = "string"
    }

    columns {
      name = "sample_id"
      type = "string"
    }

    columns {
      name = "breed"
      type = "string"
    }

    columns {
      name = "sex"
      type = "string"
    }
  }
}

# 
# Genotypes metadata
#
resource "aws_glue_catalog_table" "sbeacon-genotypes" {
  name          = "sbeacon_genotypes"
  database_name = aws_glue_catalog_database.metadata-database.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    "orc.compress" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.metadata-bucket.bucket}/genotypes"
    input_format  = "org.apache.hadoop.hive.ql.io.orc.OrcInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.orc.OrcOutputFormat"


    ser_de_info {
      name                  = "ORC"
      serialization_library = "org.apache.hadoop.hive.ql.io.orc.OrcSerde"

      parameters = {
        "serialization.format"      = 1,
        "orc.column.index.access"   = "FALSE"
        "hive.orc.use-column-names" = "TRUE"
      }
    }

    columns {
      name = "dataset_id"
      type = "string"
    }

    columns {
      name = "id_ref"
      type = "string"
    }

    columns {
      name = "sample_id"
      type = "string"
    }

    columns {
      name = "value"
      type = "string"
    }

    columns {
      name = "score"
      type = "double"
    }

    columns {
      name = "theta"
      type = "double"
    }

    columns {
      name = "b_allele_freq"
      type = "double"
    }
  }
}

# 
# Phenotypes metadata
#
resource "aws_glue_catalog_table" "sbeacon-phenotypes" {
  name          = "sbeacon_phenotypes"
  database_name = aws_glue_catalog_database.metadata-database.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    "orc.compress" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.metadata-bucket.bucket}/phenotypes"
    input_format  = "org.apache.hadoop.hive.ql.io.orc.OrcInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.orc.OrcOutputFormat"


    ser_de_info {
      name                  = "ORC"
      serialization_library = "org.apache.hadoop.hive.ql.io.orc.OrcSerde"

      parameters = {
        "serialization.format"      = 1,
        "orc.column.index.access"   = "FALSE"
        "hive.orc.use-column-names" = "TRUE"
      }
    }

    columns {
      name = "dataset_id"
      type = "string"
    }

    columns {
      name = "sample_id"
      type = "string"
    }

    columns {
      name = "sex"
      type = "string"
    }

    columns {
      name = "birth_weight_kg"
      type = "double"
    }

    columns {
      name = "weaning_weight_kg"
      type = "double"
    }

    columns {
      name = "six_month_weight_kg"
      type = "double"
    }

    columns {
      name = "fat_thickness_cm"
      type = "double"
    }

    columns {
      name = "eye_muscle_area_cm2"
      type = "double"
    }

    columns {
      name = "height_at_withers_cm"
      type = "double"
    }

    columns {
      name = "chest_girth_cm"
      type = "double"
    }

    columns {
      name = "shin_circumference_cm"
      type = "double"
    }

    columns {
      name = "pre_weaning_gain_kg"
      type = "double"
    }

    columns {
      name = "post_weaning_gain_kg"
      type = "double"
    }

    columns {
      name = "daily_weight_gain_kg"
      type = "double"
    }
  } 
}

# 
# Connected entities
# 
resource "aws_glue_catalog_table" "sbeacon-relations" {
  name          = "sbeacon_relations"
  database_name = aws_glue_catalog_database.metadata-database.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    "orc.compress" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.metadata-bucket.bucket}/relations"
    input_format  = "org.apache.hadoop.hive.ql.io.orc.OrcInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.orc.OrcOutputFormat"


    ser_de_info {
      name                  = "ORC"
      serialization_library = "org.apache.hadoop.hive.ql.io.orc.OrcSerde"

      parameters = {
        "serialization.format"      = 1,
        "orc.column.index.access"   = "FALSE"
        "hive.orc.use-column-names" = "TRUE"
      }
    }

    columns {
      name = "datasetid"
      type = "string"
    }

    columns {
      name = "cohortid"
      type = "string"
    }

    columns {
      name = "individualid"
      type = "string"
    }

    columns {
      name = "biosampleid"
      type = "string"
    }

    columns {
      name = "runid"
      type = "string"
    }

    columns {
      name = "analysisid"
      type = "string"
    }
  }
}

resource "aws_athena_workgroup" "sbeacon-workgroup" {
  name          = "query_workgroup"
  force_destroy = true

  configuration {
    enforce_workgroup_configuration    = false
    publish_cloudwatch_metrics_enabled = true

    engine_version {
      selected_engine_version = "Athena engine version 3"
    }

    result_configuration {
      output_location = "s3://${aws_s3_bucket.metadata-bucket.bucket}/query-results/"
    }
  }
}

#
# Glue crawler IAM policies
# Official docs are not super complete refer to below
# https://www.xerris.com/insights/building-modern-data-warehouses-with-s3-glue-and-athena-part-3/
#
resource "aws_iam_role" "glue_role" {
  name               = "glue_role"
  assume_role_policy = data.aws_iam_policy_document.glue.json
}

data "aws_iam_policy_document" "glue" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["glue.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "extra-glue-policy-document" {
  statement {
    actions = [
    "s3:GetBucketLocation", "s3:ListBucket", "s3:ListAllMyBuckets", "s3:GetBucketAcl", "s3:GetObject"]
    resources = [
      "arn:aws:s3:::${aws_s3_bucket.metadata-bucket.bucket}",
      "arn:aws:s3:::${aws_s3_bucket.metadata-bucket.bucket}/*"
    ]
  }
}

resource "aws_iam_policy" "extra-glue-policy" {
  name        = "extra-glue-policy"
  description = "Extra permissions"
  policy      = data.aws_iam_policy_document.extra-glue-policy-document.json

}

resource "aws_iam_role_policy_attachment" "glue-extra-policy-attachment" {
  role       = aws_iam_role.glue_role.name
  policy_arn = aws_iam_policy.extra-glue-policy.arn
}

data "aws_iam_policy" "AWSGlueServiceRole" {
  arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_iam_role_policy_attachment" "glue-service-role-attachment" {
  role       = aws_iam_role.glue_role.name
  policy_arn = data.aws_iam_policy.AWSGlueServiceRole.arn
}
