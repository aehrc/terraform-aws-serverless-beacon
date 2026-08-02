# 
# Metadata tables on AWS Athena
# AWS docs to refer;
# SerDe types from https://docs.aws.amazon.com/athena/latest/ug/athena-ug.pdf
# Glue docs; https://docs.aws.amazon.com/glue/latest/dg/glue-dg.pdf
# Athena does not support - in database names, use _ instead
#

# 
# SNPs metadata
#
resource "aws_glue_catalog_table" "sbeacon-snps-cache" {
  name          = "sbeacon_snps_cache"
  database_name = aws_glue_catalog_database.metadata-database.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    "orc.compress" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.metadata-bucket.bucket}/snps-cache"
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
      type = "string"
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
resource "aws_glue_catalog_table" "sbeacon-samples-cache" {
  name          = "sbeacon_samples_cache"
  database_name = aws_glue_catalog_database.metadata-database.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    "orc.compress" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.metadata-bucket.bucket}/samples-cache"
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
resource "aws_glue_catalog_table" "sbeacon-genotypes-cache" {
  name          = "sbeacon_genotypes_cache"
  database_name = aws_glue_catalog_database.metadata-database.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    "orc.compress" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.metadata-bucket.bucket}/genotypes-cache"
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
      type = "string"
    }

    columns {
      name = "theta"
      type = "string"
    }

    columns {
      name = "b_allele_freq"
      type = "string"
    }
  }
}

# 
# Phenotypes metadata
#
resource "aws_glue_catalog_table" "sbeacon-phenotypes-cache" {
  name          = "sbeacon_phenotypes_cache"
  database_name = aws_glue_catalog_database.metadata-database.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    "orc.compress" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.metadata-bucket.bucket}/phenotypes-cache"
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
      type = "string"
    }

    columns {
      name = "weaning_weight_kg"
      type = "string"
    }

    columns {
      name = "six_month_weight_kg"
      type = "string"
    }

    columns {
      name = "fat_thickness_cm"
      type = "string"
    }

    columns {
      name = "eye_muscle_area_cm2"
      type = "string"
    }

    columns {
      name = "height_at_withers_cm"
      type = "string"
    }

    columns {
      name = "chest_girth_cm"
      type = "string"
    }

    columns {
      name = "shin_circumference_cm"
      type = "string"
    }

    columns {
      name = "pre_weaning_gain_kg"
      type = "string"
    }

    columns {
      name = "post_weaning_gain_kg"
      type = "string"
    }

    columns {
      name = "daily_weight_gain_kg"
      type = "string"
    }
  } 
}

# 
# Ontology terms cache - used to build proper index later on
# 
resource "aws_glue_catalog_table" "sbeacon-terms-cache" {
  name          = "sbeacon_terms_cache"
  database_name = aws_glue_catalog_database.metadata-database.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    "orc.compress" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.metadata-bucket.bucket}/terms-cache"
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
      name = "kind"
      type = "string"
    }

    columns {
      name = "id"
      type = "string"
    }

    columns {
      name = "term"
      type = "string"
    }

    columns {
      name = "label"
      type = "string"
    }

    columns {
      name = "type"
      type = "string"
    }
  }
}
