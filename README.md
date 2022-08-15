# Serverless Beacon

## Why serverless?
Serverless means the service does not require any servers to be provisioned. The
idea is to minimise running costs, as well as support arbitrary scalablility. It
also means setup is very fast.

## Beacon
The service intends to support beacon v2 according to the
[ga4gh specification](https://github.com/ga4gh-beacon/specification).

## Installation

### The environment

Run the following shell commands to setup necessary build tools. Valid for Amazon Linux development instances.

```sh
# install development essentials
sudo yum install -y gcc10 gcc10-c++ git openssl-devel libcurl-devel
sudo ln -s /usr/bin/gcc10-gcc /usr/bin/gcc
sudo ln -s /usr/bin/gcc10-g++ /usr/bin/g++

# Install CMake
wget https://cmake.org/files/v3.20/cmake-3.20.3.tar.gz
tar -xvzf cmake-3.20.3.tar.gz
cd cmake-3.20.3
./bootstrap
make
sudo make install
```

### Deployment

Clone the codebase from our repository to your local machine (or EC2). Make sure you export the AWS access keys or you're running from an AWS IAM power access authorized EC2 instance.

```sh
git clone https://github.com/aehrc/terraform-aws-serverless-beacon.git
cd terraform-aws-serverless-beacon
```

Now set the AWS access keys and token as needed.
```sh
export AWS_ACCESS_KEY_ID="AWS_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="AWS_SECRET_ACCESS_KEY"
export AWS_SESSION_TOKEN="AWS_SESSION_TOKEN"
```

Install using `terraform init` to pull the module, followed by running `terraform apply` will create the infrastucture. For adding data to the beacon, see the API. To shut down the entire service run `terraform destroy`. Any created datasets
will be lost (but not the VCFs on which they are based).

```sh
terraform init
terraform plan # should finish without errors
terraform apply
```

### Development

All the layers needed for the program to run are in layers folder. To add a new layer for immediate use with additional configs, run the following commands.

* Python layer
```sh
cd terraform-aws-serverless-beacon
pip install --target layers/<Library Name>/python <Library Name>
```

* Binary layer
```sh
# clone the repo somewhere else
git clone <REPO> 
cd <REPO>
mkdir build && cd build && cmake .. && make && make install
# copy the bin and lib folders to a folder inside layers
cp bin terraform-aws-serverless-beacon/layers/<Library Name>/
cp lib terraform-aws-serverless-beacon/layers/<Library Name>/
# troubleshoot with "ldd ./binary-name" to see what libaries needed
```

* Collaborative development

Please make a copy of `backend.tf.template` with suited parameters and rename as `backend.tf`. Refer to documentation for more information [https://www.terraform.io/language/settings/backends/configuration](https://www.terraform.io/language/settings/backends/configuration).

## API

### Data ingestion API

* Submit dataset - please follow the JSON schema at [./lambda/submitDataset/new-schema.json](./lambda/submitDataset/new-schema.json)
* Update dataset - please follow the JSON schema at [./lambda/submitDataset/update-schema.json](./lambda/submitDataset/update-schema.json)

### Query API

Querying is available as per API defined by BeaconV2 [https://beacon-project.io/#the-beacon-v2-model](https://beacon-project.io/#the-beacon-v2-model). 
* All the available endpoints can be retrieved using the deployment url's `/map`. 
* Schema for beacon V2 configuration can be obtained from `/configuration`.
* Entry types are defined at `/entry_types`.

### Implemented Endpoints

#### Variant searching

* GET/POST `/g_variants` - variant querying
* GET/POST `/g_variants/{id}` - Search for unique variants 
* GET/POST `/g_variants/{id}/biosamples` - Biosamples having the unique variant
* GET/POST `/g_variants/{id}/individuals` - Individuals having the unique variant

#### Generic Endpoints
* GET/POST `/` or `/info` - get beacon information
* GET/POST `/map` - get beacon map
* GET/POST `/filtering_terms` - get ontology terms
* GET/POST `/entry_types` - get types returned by the beacon

#### In-progress

* Individuals
* Biosamples

<!-- under development -->

<!-- ## Known Issues
##### Variants may not be found if the reference sequence contains a padding base
For example if a deletion A > . in position 5 (1 based), is searched for, it is
represented in a vcf as eg 4 GA G and will not be discovered. It will be
discovered if it is queried as GA > G in position 4.

## To do
##### Implement general security for registered and controlled datasets
* Allow the security level to be set on a dataset
* Implement OAuth2 for dataset access
##### Implement better frequency calculations for distributed datasets
If a vcf does not represent a variant, no calls are added for the purposes of
calculating allele frequency. This means that if there are multiple
single-sample vcfs, each hit allele will ignore any samples that don't show the
variant, resulting in frequencies calculated using only heterozygotes and
homozygotes for the alternate allele. -->
