provider "aws" {
  region = "ap-southeast-2"
}

module "serverless-beacon" {
  source = "../.."
  beacon-id = "au.csiro-serverless.beacon"
  beacon-name = "CSIRO Serverless Beacon"
  organisation-id = "CSIRO"
  organisation-name = "CSIRO"
  common-tags = {
    stack = "serverless-beacon"
    environment = "dev"
  }
}
