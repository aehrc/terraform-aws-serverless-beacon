variable "beacon-id" {
  type = string
  description = "Unique identifier of the beacon. Use reverse domain name notation."
}

variable "beacon-name" {
  type = string
  description = "Human readable name of the beacon."
}

variable "organisation-id" {
  type = string
  description = "Unique identifier of the organization providing the beacon."
}

variable "organisation-name" {
  type = string
  description = "Name of the organization providing the beacon."
}

variable "common-tags" {
  type = map(string)
  description = "A set of tags to attach to every created resource."
  default = {}
}
