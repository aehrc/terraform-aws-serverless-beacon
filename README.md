# Serverless Beacon

## Why serverless?
Serverless means the service does not require any servers to be provisioned. The
idea is to minimise running costs, as well as support arbitrary scalablility. It
also means setup is very fast.

## Beacon
The service intends to support beacon v1 according to the
[ga4gh specification](https://github.com/ga4gh-beacon/specification).

## Installation
To package the code for lambda functions run `pre-terraform-build.sh`.
Install using `terraform init` followed by `terraform apply`. For adding data to
the beacon, see the API.

To shut down the entire service run `terraform destroy`. Any created datasets
will be lost (but not the VCFs on which they are based).

## API
The result of `terraform apply` or `terraform output` will be the base URL of
the API. The main query API is designed to be compatible with the ga4gh Beacon
API, with an additional endpoint `/submit` for the purposes of adding or editing
datasets. The API is contained in `openapi.yaml`.

## Known Issues
##### Cannot run terraform apply, Global Secondary Index missing required fields.
This is a bug in v1.51.0 of the aws provider for terraform. There is a fix
available on the `dynamo-on-demand-gsi-fix` branch at
`https://github.com/sbogacz/terraform-provider-aws`, which is a Go project, the
result of which must replace the aws plugin binary in `.terraform/plugins`.

## To do
##### Allow use of startMin, startMax, endMin and endMax
* Allow querying regions based on these variables.
* Split performQuery lambda function so each function only queries a small
slice.
##### Allow multiple VCFs in a single dataset
* Split performQuery so each function only queries a single VCF, see above.
* Set up the `/submit` endpoint to be able to handle vcfLocations as an array
##### Implement security for calls to `/submit`
##### Implement general security for registered and controlled datasets
* Allow the security level to be set on a dataset
* Implement OAuth2 for dataset access
