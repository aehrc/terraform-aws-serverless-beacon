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
# Cohorts metadata
# 
resource "aws_glue_catalog_table" "sbeacon-cohorts" {
  name          = "sbeacon_cohorts"
  database_name = aws_glue_catalog_database.metadata-database.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    "orc.compress" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.metadata-bucket.bucket}/cohorts"
    input_format = "org.apache.hadoop.hive.ql.io.orc.OrcInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.orc.OrcOutputFormat"


    ser_de_info {
      name                  = "ORC"
      serialization_library = "org.apache.hadoop.hive.ql.io.orc.OrcSerde"

      parameters = {
        "serialization.format" = 1,
        "orc.column.index.access" = "FALSE"
        "hive.orc.use-column-names" = "TRUE"
      }
    }

    columns {
      name = "id"
      type = "string"
    }

    columns {
      name = "cohortdatatypes"
      type = "string"
    }

    columns {
      name = "cohortdesign"
      type = "string"
    }

    columns {
      name = "cohortsize"
      type = "string"
    }

    columns {
      name = "cohorttype"
      type = "string"
    }

    columns {
      name = "collectionevents"
      type = "string"
    }

    columns {
      name = "exclusioncriteria"
      type = "string"
    }

    columns {
      name = "inclusioncriteria"
      type = "string"
    }

    columns {
      name = "name"
      type = "string"
    }
  }
}

# 
# Datasets metadata
# 
resource "aws_glue_catalog_table" "sbeacon-datasets" {
  name          = "sbeacon_datasets"
  database_name = aws_glue_catalog_database.metadata-database.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    "orc.compress" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.metadata-bucket.bucket}/datasets"
    input_format = "org.apache.hadoop.hive.ql.io.orc.OrcInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.orc.OrcOutputFormat"


    ser_de_info {
      name                  = "ORC"
      serialization_library = "org.apache.hadoop.hive.ql.io.orc.OrcSerde"

      parameters = {
        "serialization.format" = 1,
        "orc.column.index.access" = "FALSE"
        "hive.orc.use-column-names" = "TRUE"
      }
    }

    columns {
      name = "id"
      type = "string"
    }

    columns {
      name = "_assemblyid"
      type = "string"
    }
    
    columns {
      name = "_vcflocations"
      type = "string"
    }

    columns {
      name = "_vcfchromosomemap"
      type = "string"
    }

    columns {
      name = "createdatetime"
      type = "string"
    }

    columns {
      name = "datauseconditions"
      type = "string"
    }

    columns {
      name = "description"
      type = "string"
    }

    columns {
      name = "externalurl"
      type = "string"
    }

    columns {
      name = "info"
      type = "string"
    }

    columns {
      name = "name"
      type = "string"
    }

    columns {
      name = "updatedatetime"
      type = "string"
    }

    columns {
      name = "version"
      type = "string"
    }
  }
}

# 
# Individuals metadata
# 
resource "aws_glue_catalog_table" "sbeacon-individuals" {
  name          = "sbeacon_individuals"
  database_name = aws_glue_catalog_database.metadata-database.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    "orc.compress" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.metadata-bucket.bucket}/individuals"
    input_format = "org.apache.hadoop.hive.ql.io.orc.OrcInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.orc.OrcOutputFormat"


    ser_de_info {
      name                  = "ORC"
      serialization_library = "org.apache.hadoop.hive.ql.io.orc.OrcSerde"

      parameters = {
        "serialization.format" = 1,
        "orc.column.index.access" = "FALSE"
        "hive.orc.use-column-names" = "TRUE"
      }
    }

    columns {
      name = "id"
      type = "string"
    }

    columns {
      name = "_datasetid"
      type = "string"
    }

    columns {
      name = "_cohortid"
      type = "string"
    }

    columns {
      name = "diseases"
      type = "string"
    }

    columns {
      name = "ethnicity"
      type = "string"
    }

    columns {
      name = "exposures"
      type = "string"
    }

    columns {
      name = "geographicorigin"
      type = "string"
    }

    columns {
      name = "info"
      type = "string"
    }

    columns {
      name = "interventionsorprocedures"
      type = "string"
    }

    columns {
      name = "karyotypicsex"
      type = "string"
    }

    columns {
      name = "measures"
      type = "string"
    }

    columns {
      name = "pedigrees"
      type = "string"
    }

    columns {
      name = "phenotypicfeatures"
      type = "string"
    }

    columns {
      name = "sex"
      type = "string"
    }

    columns {
      name = "treatments"
      type = "string"
    }
  }
}

# 
# Biosamples metadata
# 
resource "aws_glue_catalog_table" "sbeacon-biosamples" {
  name          = "sbeacon_biosamples"
  database_name = aws_glue_catalog_database.metadata-database.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    "orc.compress" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.metadata-bucket.bucket}/biosamples"
    input_format = "org.apache.hadoop.hive.ql.io.orc.OrcInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.orc.OrcOutputFormat"


    ser_de_info {
      name                  = "ORC"
      serialization_library = "org.apache.hadoop.hive.ql.io.orc.OrcSerde"

      parameters = {
        "serialization.format" = 1,
        "orc.column.index.access" = "FALSE"
        "hive.orc.use-column-names" = "TRUE"
      }
    }
    columns {
      name = "id"
      type = "string"
    }

    columns {
      name = "_datasetid"
      type = "string"
    }

    columns {
      name = "_cohortid"
      type = "string"
    }

    columns {
      name = "individualid"
      type = "string"
    }

    columns {
      name = "biosamplestatus"
      type = "string"
    }

    columns {
      name = "collectiondate"
      type = "string"
    }

    columns {
      name = "collectionmoment"
      type = "string"
    }

    columns {
      name = "diagnosticmarkers"
      type = "string"
    }

    columns {
      name = "histologicaldiagnosis"
      type = "string"
    }

    columns {
      name = "measurements"
      type = "string"
    }

    columns {
      name = "obtentionprocedure"
      type = "string"
    }

    columns {
      name = "pathologicalstage"
      type = "string"
    }

    columns {
      name = "pathologicaltnmfinding"
      type = "string"
    }

    columns {
      name = "phenotypicfeatures"
      type = "string"
    }

    columns {
      name = "sampleorigindetail"
      type = "string"
    }

    columns {
      name = "sampleorigintype"
      type = "string"
    }

    columns {
      name = "sampleprocessing"
      type = "string"
    }

    columns {
      name = "samplestorage"
      type = "string"
    }

    columns {
      name = "tumorgrade"
      type = "string"
    }

    columns {
      name = "tumorprogression"
      type = "string"
    }

    columns {
      name = "info"
      type = "string"
    }

    columns {
      name = "notes"
      type = "string"
    }
  }
}

# 
# Runs metadata
# 
resource "aws_glue_catalog_table" "sbeacon-runs" {
  name          = "sbeacon_runs"
  database_name = aws_glue_catalog_database.metadata-database.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    "orc.compress" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.metadata-bucket.bucket}/runs"
    input_format = "org.apache.hadoop.hive.ql.io.orc.OrcInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.orc.OrcOutputFormat"


    ser_de_info {
      name                  = "ORC"
      serialization_library = "org.apache.hadoop.hive.ql.io.orc.OrcSerde"

      parameters = {
        "serialization.format" = 1,
        "orc.column.index.access" = "FALSE"
        "hive.orc.use-column-names" = "TRUE"
      }
    }

    columns {
      name = "id"
      type = "string"
    }

    columns {
      name = "_datasetid"
      type = "string"
    }

    columns {
      name = "_cohortid"
      type = "string"
    }

    columns {
      name = "biosampleid"
      type = "string"
    }

    columns {
      name = "individualid"
      type = "string"
    }

    columns {
      name = "info"
      type = "string"
    }

    columns {
      name = "librarylayout"
      type = "string"
    }

    columns {
      name = "libraryselection"
      type = "string"
    }

    columns {
      name = "librarysource"
      type = "string"
    }

    columns {
      name = "librarystrategy"
      type = "string"
    }

    columns {
      name = "platform"
      type = "string"
    }

    columns {
      name = "platformmodel"
      type = "string"
    }

    columns {
      name = "rundate"
      type = "string"
    }
  }
}

# 
# Analyses metadata
# 
resource "aws_glue_catalog_table" "sbeacon-analyses" {
  name          = "sbeacon_analyses"
  database_name = aws_glue_catalog_database.metadata-database.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    "orc.compress" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.metadata-bucket.bucket}/analyses"
    input_format = "org.apache.hadoop.hive.ql.io.orc.OrcInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.orc.OrcOutputFormat"


    ser_de_info {
      name                  = "ORC"
      serialization_library = "org.apache.hadoop.hive.ql.io.orc.OrcSerde"

      parameters = {
        "serialization.format" = 1,
        "orc.column.index.access" = "FALSE"
        "hive.orc.use-column-names" = "TRUE"
      }
    }
    
    columns {
      name = "id"
      type = "string"
    }

    columns {
      name = "_datasetid"
      type = "string"
    }

    columns {
      name = "_cohortid"
      type = "string"
    }

    columns {
      name = "_vcfsampleid"
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
      name = "aligner"
      type = "string"
    }

    columns {
      name = "analysisdate"
      type = "string"
    }

    columns {
      name = "info"
      type = "string"
    }

    columns {
      name = "pipelinename"
      type = "string"
    }

    columns {
      name = "pipelineref"
      type = "string"
    }

    columns {
      name = "variantcaller"
      type = "string"
    }
  }
}

# 
# Ontology terms index
# 
resource "aws_glue_catalog_table" "sbeacon-terms-index" {
  name          = "sbeacon_terms_index"
  database_name = aws_glue_catalog_database.metadata-database.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    "orc.compress" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.metadata-bucket.bucket}/terms_index"
    input_format = "org.apache.hadoop.hive.ql.io.orc.OrcInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.orc.OrcOutputFormat"


    ser_de_info {
      name                  = "ORC"
      serialization_library = "org.apache.hadoop.hive.ql.io.orc.OrcSerde"

      parameters = {
        "serialization.format" = 1,
        "orc.column.index.access" = "FALSE"
        "hive.orc.use-column-names" = "TRUE"
      }
    }
    
    columns {
      name = "id"
      type = "string"
    }

    columns {
      name = "term"
      type = "string"
    }
  }

  partition_keys {
    comment = "partition by kind"
    name = "kind"
    type = "string"
  }
}

# 
# Ontology terms (for pagination and filtering)
# 
resource "aws_glue_catalog_table" "sbeacon-terms" {
  name          = "sbeacon_terms"
  database_name = aws_glue_catalog_database.metadata-database.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    "orc.compress" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.metadata-bucket.bucket}/terms"
    input_format = "org.apache.hadoop.hive.ql.io.orc.OrcInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.orc.OrcOutputFormat"


    ser_de_info {
      name                  = "ORC"
      serialization_library = "org.apache.hadoop.hive.ql.io.orc.OrcSerde"

      parameters = {
        "serialization.format" = 1,
        "orc.column.index.access" = "FALSE"
        "hive.orc.use-column-names" = "TRUE"
      }
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

  partition_keys {
    comment = "partition by kind"
    name = "kind"
    type = "string"
  }
}

resource "aws_glue_crawler" "sbeacon-crawler" {
  database_name = aws_glue_catalog_database.metadata-database.name
  name          = "sbeacon-crawler"
  role          = aws_iam_role.glue_role.arn

  catalog_target {
    database_name = aws_glue_catalog_database.metadata-database.name
    tables        = [
      aws_glue_catalog_table.sbeacon-individuals.name,
      aws_glue_catalog_table.sbeacon-biosamples.name
    ]
  }

  schema_change_policy {
    delete_behavior = "LOG"
  }

  configuration = <<EOF
{
  "Version":1.0,
  "Grouping": {
    "TableGroupingPolicy": "CombineCompatibleSchemas"
  },
  "CrawlerOutput": {
      "Partitions": { "AddOrUpdateBehavior": "InheritFromTable" }
   }
}
EOF
}

resource "aws_athena_workgroup" "sbeacon-workgroup" {
  name          = "query_workgroup"
  force_destroy = true

  configuration {
    enforce_workgroup_configuration    = false
    publish_cloudwatch_metrics_enabled = true

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
