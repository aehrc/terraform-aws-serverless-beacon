# Serverless Beacon

## Why serverless?
Serverless means the service does not require any servers to be provisioned. The
idea is to minimise running costs, as well as support arbitrary scalablility. It
also means setup is very fast.

## Beacon
The service intends to support beacon v1 according to the
[ga4gh specification](https://github.com/ga4gh-beacon/specification).

## Installation
Install using `terraform init` to pull the module, followed by running
`pre-terraform-build.sh` from inside the module's directory. This will build the
zip packages for the lambda functions and need only be done once.
Running `terraform apply` will create the infrastucture.
For adding data to the beacon, see the API.

To shut down the entire service run `terraform destroy`. Any created datasets
will be lost (but not the VCFs on which they are based).

To repackage the code for lambda functions (if any customisations are made) run
`pre-terraform-build.sh` followed by `terraform apply`.

For standalone use the aws provider will need to be added in main.tf. See the
example for more information.


## API
The result of `terraform apply` or `terraform output` will be the base URL of
the API. The main query API is designed to be compatible with the ga4gh Beacon
API, with an additional endpoint `/submit` for the purposes of adding or editing
datasets. The API is contained in `openapi.yaml`.

## Known Issues
##### Cannot run terraform apply, Global Secondary Index missing required fields.
This is a bug in v1.51.0 of the aws provider for terraform. The AWS provider
plugin must be updated to v1.52.0 using `terraform init --upgrade`
##### Variants may not be found if the reference sequence contains a padding base
For example if a deletion A > . in position 5 (1 based), is searched for, it is
represented in a vcf as eg 4 GA G and will not be discovered. It will be
discovered if it is queried as GA > G in position 4.

## To do
##### Implement security for calls to `/submit`
##### Implement general security for registered and controlled datasets
* Allow the security level to be set on a dataset
* Implement OAuth2 for dataset access
##### Implement better frequency calculations for distributed datasets
If a vcf does not represent a variant, no calls are added for the purposes of
calculating allele frequency. This means that if there are multiple
single-sample vcfs, each hit allele will ignore any samples that don't show the
variant, resulting in frequencies calculated using only heterozygotes and
homozygotes for the alternate allele.
