# AWS region variable
variable "region" {
  type        = string
  description = "Deployment region."
  default     = "us-east-1"
}

# AWS configuration
variable "common-tags" {
  type        = map(string)
  description = "A set of tags to attach to every created resource."
  default     = {}
}

variable "variants-bucket-prefix" {
  type        = string
  description = "S3 bucket for storing vcf summaries used for duplicate variant searches"
  default     = "sbeacon-variants-"
}

variable "metadata-bucket-prefix" {
  type        = string
  description = "S3 bucket for storing metadata"
  default     = "sbeacon-metadata-"
}

variable "lambda-layers-bucket-prefix" {
  type        = string
  description = "S3 bucket for storing lambda layers"
  default     = "sbeacon-lambda-layers-"
}

# Beacon variables
variable "beacon-id" {
  type        = string
  description = "Unique identifier of the beacon. Use reverse domain name notation."
  default     = "au.csiro.sbeacon"
}

variable "beacon-name" {
  type        = string
  description = "Human readable name of the beacon."
  default     = "CSIRO Serverless Beacon"
}

variable "beacon-api-version" {
  type        = string
  description = "Value for beacon api version"
  default     = "v2.0.0"
}

variable "beacon-environment" {
  type        = string
  description = "Value for beacon environment"
  default     = "dev"
}

variable "beacon-description" {
  type        = string
  description = "Value for beacon description"
  default     = "Serverless Beacon (sBeacon)"
}

variable "beacon-version" {
  type        = string
  description = "Value for beacon version"
  default     = "v0.1.0"
}

variable "beacon-welcome-url" {
  type        = string
  description = "Value for beacon welcome url"
  default     = "https://bioinformatics.csiro.au/"
}

variable "beacon-alternative-url" {
  type        = string
  description = "Value for beacon alternative url"
  default     = "https://bioinformatics.csiro.au/"
}

variable "beacon-create-datetime" {
  type        = string
  description = "Value for beacon create datetime"
  default     = "2018-11-26H00:00:00Z"
}

variable "beacon-update-datetime" {
  type        = string
  description = "Value for beacon update datetime"
  default     = "2023-03-16H00:00:00Z"
}

variable "beacon-handovers" {
  type        = string
  description = "Value for beacon handovers (use a stringified array)"
  default     = "[]"
}

variable "beacon-documentation-url" {
  type        = string
  description = "Value for beacon documentation url"
  default     = "https://github.com/EGA-archive/beacon2-ri-api"
}

variable "beacon-default-granularity" {
  type        = string
  description = "Value for beacon default granularity"
  default     = "boolean"
}

variable "beacon-uri" {
  type        = string
  description = "Value for beacon-uri"
  default     = "https://beacon.csiro.au"
}

# Organisation variables
variable "organisation-id" {
  type        = string
  description = "Unique identifier of the organisation providing the beacon."
  default     = "CSIRO"
}

variable "organisation-name" {
  type        = string
  description = "Name of the organisation providing the beacon."
  default     = "CSIRO"
}

variable "beacon-org-description" {
  type        = string
  description = "Value for beacon organisation description"
  default     = "CSIRO, Australia"
}

variable "beacon-org-address" {
  type        = string
  description = "Value for beacon orgisation adress"
  default     = "AEHRC, Westmead NSW, Australia"
}

variable "beacon-org-welcome-url" {
  type        = string
  description = "Value for beacon organisation welcome url"
  default     = "https://beacon.csiro.au"
}

variable "beacon-org-contact-url" {
  type        = string
  description = "Value for beacon organisation contact url"
  default     = "https://bioinformatics.csiro.au/get-in-touch/"
}

variable "beacon-org-logo-url" {
  type        = string
  description = "Value for beacon organisation logo url"
  default     = "https://bioinformatics.csiro.au/covid-19-sbeacon/"
}

# Beacon service variables
variable "beacon-service-type-group" {
  type        = string
  description = "Value for beacon service type group"
  default     = "au.csiro"
}

variable "beacon-service-type-artifact" {
  type        = string
  description = "Value for beacon service type artifact"
  default     = "beacon"
}

variable "beacon-service-type-version" {
  type        = string
  description = "Value for beacon service type version"
  default     = "1.0"
}
