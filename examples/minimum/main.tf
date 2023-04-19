module "serverless-beacon" {
  source                      = "../.."
  beacon-id                   = "au.csiro-serverless.beacon"
  variants-bucket-prefix      = "sbeacon-"
  metadata-bucket-prefix      = "sbeacon-metadata-"
  lambda-layers-bucket-prefix = "sbeacon-lambda-layers-"
  beacon-name                 = "CSIRO Serverless Beacon"
  organisation-id             = "CSIRO"
  organisation-name           = "CSIRO"
}
