variable "beacon-id" {
  type         = string
  description  = "Unique identifier of the beacon. Use reverse domain name notation."
  default      = "sbeacon.csiro.au"
}

variable "beacon-name" {
  type         = string
  description  = "Human readable name of the beacon."
  default      = "CSIRO Serverless Beacon"
}

variable "organisation-id" {
  type         = string
  description  = "Unique identifier of the organization providing the beacon."
  default      = "CSIRO"
}

variable "organisation-name" {
  type         = string
  description  = "Name of the organization providing the beacon."
  default      = "CSIRO"
}

variable "common-tags" {
  type         = map(string)
  description  = "A set of tags to attach to every created resource."
  default      = {}
}

variable "variants-bucket-prefix" {
  type         = string
  description  = "S3 bucket for storing vcf summaries used for duplicate variant searches"
  default      = "sbeacon-variants-"
}

variable "metadata-bucket-prefix" {
  type         = string
  description  = "S3 bucket for storing metadata"
  default      = "sbeacon-metadata-"
}

variable "lambda-layers-bucket-prefix" {
  type         = string
  description  = "S3 bucket for storing lambda layers"
  default      = "sbeacon-lambda-layers-"
}
