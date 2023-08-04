# 
# Metadata tables on AWS Athena
# AWS docs to refer;
# SerDe types from https://docs.aws.amazon.com/athena/latest/ug/athena-ug.pdf
# Glue docs; https://docs.aws.amazon.com/glue/latest/dg/glue-dg.pdf
# Athena does not support - in database names, use _ instead
#

# 
# Cohorts metadata
# 
resource "aws_glue_catalog_table" "sbeacon-cohorts-cache" {
  name          = "sbeacon_cohorts_cache"
  database_name = aws_glue_catalog_database.metadata-database.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    "orc.compress" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.metadata-bucket.bucket}/cohorts-cache"
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
      type = "int"
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
resource "aws_glue_catalog_table" "sbeacon-datasets-cache" {
  name          = "sbeacon_datasets_cache"
  database_name = aws_glue_catalog_database.metadata-database.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    "orc.compress" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.metadata-bucket.bucket}/datasets-cache"
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
resource "aws_glue_catalog_table" "sbeacon-individuals-cache" {
  name          = "sbeacon_individuals_cache"
  database_name = aws_glue_catalog_database.metadata-database.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    "orc.compress" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.metadata-bucket.bucket}/individuals-cache"
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
resource "aws_glue_catalog_table" "sbeacon-biosamples-cache" {
  name          = "sbeacon_biosamples_cache"
  database_name = aws_glue_catalog_database.metadata-database.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    "orc.compress" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.metadata-bucket.bucket}/biosamples-cache"
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
resource "aws_glue_catalog_table" "sbeacon-runs-cache" {
  name          = "sbeacon_runs_cache"
  database_name = aws_glue_catalog_database.metadata-database.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    "orc.compress" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.metadata-bucket.bucket}/runs-cache"
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
resource "aws_glue_catalog_table" "sbeacon-analyses-cache" {
  name          = "sbeacon_analyses_cache"
  database_name = aws_glue_catalog_database.metadata-database.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL       = "TRUE"
    "orc.compress" = "SNAPPY"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.metadata-bucket.bucket}/analyses-cache"
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
