provider "aws" {
  region = "${var.region}"
}

module "beacon-api" {
  source = "modules/beacon-api"
}
