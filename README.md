<!-- TOC --><a name="serverless-beacon"></a>
## Serverless Beacon
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

<p align="center">
  <img src="assets/logo-black.png" alt="sbacon" width="600">
</p>

<!-- TOC start (generated with https://github.com/derlin/bitdowntoc) -->

- [Serverless Beacon](#serverless-beacon)
- [Why serverless?](#why-serverless)
- [Introduction to sBeacon](#introduction-to-sbeacon)
- [Installation](#installation)
   * [Option 1: Setting up the development environment on Amazon Linux](#option-1-setting-up-the-development-environment-on-amazon-linux)
   * [Option 2: Using the docker image](#option-2-using-the-docker-image)
   * [Option 3 (Recommended): Using the VSCODE dev containers](#option-3-using-the-vscode-dev-containers)
- [Deployment](#deployment)
   * [Direct deployment](#direct-deployment)
   * [Use as a module](#use-as-a-module)
- [Development](#development)
- [API Usage](#api-usage)
   * [Example data](#example-data)
   * [Data ingestion API](#data-ingestion-api)
   * [Query API](#query-api)
- [Securing the API](#securing-the-api)
- [Troubleshooting](#troubleshooting)
   * [Docker error (invalid reference format)](#docker-error-invalid-reference-format)
   * [Illegal instruction (core dumped)](#illegal-instruction-core-dumped)
   * [Provider produced inconsistent final plan](#provider-produced-inconsistent-final-plan)
   * [Updating partition_keys schema in glue.catalog_table according to AWS documentation](#updating-partition_keys-schema-in-gluecatalog_table-according-to-aws-documentation)

<!-- TOC end -->

<!-- TOC --><a name="why-serverless"></a>
## Why serverless?
Serverless means the service does not require any servers to be provisioned. The
idea is to minimise running costs, as well as support arbitrary scalablility. It
also means setup is very fast.

<!-- TOC --><a name="introduction-to-sbeacon"></a>
## Introduction to sBeacon
sBeacon implements Beacon v2 protocol according to the
[ga4gh specification](https://github.com/ga4gh-beacon/specification). sBeacon can be used as a beacon network participant. Please refer to [https://docs.genomebeacons.org/networks/](https://docs.genomebeacons.org/networks/).

<!-- TOC --><a name="installation"></a>
## Installation

You can use either local development or a docker environment for development and deployment. First download the repository using the following command. If you're missing the `git` command please have a look at the **Option 1** commands.

```bash
# use following or the bitbucket if you have access to it
git clone https://github.com/aehrc/terraform-aws-serverless-beacon.git
cd terraform-aws-serverless-beacon
```

<!-- TOC --><a name="option-1-setting-up-the-development-environment-on-amazon-linux"></a>
### Option 1: Setting up the development environment on Amazon Linux

Note: the following instructions are strictly for `Amazon Linux 2023 AMI 2023.0.20230419.0 x86_64 HVM kernel-6.1` AMI with name `al2023-ami-2023.0.20230419.0-kernel-6.1-x86_64`.

Skip to next section if you're only interested in deployment or using a different architecture compared to AWS lambda environment. The following setup must be performed on a latest Amazon Linux instance to match the lambda runtimes. If this is not a viable option, please resort to using Docker.

Run the following shell commands to setup necessary build tools. Valid for Amazon Linux development instances.

Required dependencies
* Compressionlibraries `xz`, `bzip2` and `zlib`
* Exact python version - `Python3.12`

Install system-wide dependencies

```bash
# Install development essentials
sudo yum update
sudo yum upgrade
sudo yum install -y git openssl-devel libcurl-devel wget bzip2-devel xz-devel libffi-devel zlib-devel autoconf intltool 
```

Install `Python 3.12` to a virtual environment
```bash
# Download and install python
cd ~
wget https://www.python.org/ftp/python/3.12.5/Python-3.12.5.tgz

tar xzf Python-3.12.5.tgz
cd Python-3.12.5
./configure --enable-optimizations
sudo make altinstall

cd ~
python3.12 -m venv py312

# activate py312 environment
source ~/py312/bin/activate 
```

Make sure you have the terraform version `Terraform v1.9.4` or newer if you're not using the docker image. Run the following command to get the terraform binary.

```bash
# only for linux - find other OS version here https://releases.hashicorp.com/terraform/1.9.4/
cd ~
wget https://releases.hashicorp.com/terraform/1.9.4/terraform_1.9.4_linux_amd64.zip
sudo unzip terraform_1.9.4_linux_amd64.zip -d /usr/bin/
```

<!-- TOC --><a name="option-2-using-the-docker-image"></a>
### Option 2: Using the docker image

Initialise the docker container using the following command.

```bash
# on x86_64 machines
docker build -t csiro/sbeacon ./docker
# on aarch64
docker build --platform linux/amd64  -t csiro/sbeacon ./docker
```

This will initialise the docker container that contains everything you need including terraform. In order to start the docker container from within the repository directory run the following command.

```bash
docker run --rm -it -v `pwd`:`pwd` -v /var/run/docker.sock:/var/run/docker.sock  -w `pwd` --platform linux/x86_64 csiro/sbeacon:latest /bin/bash
```

<!-- TOC --><a name="option-3-using-the-vscode-dev-containers"></a>
### Option 3: Using the VSCODE dev containers

Your system must have docker installed with the active user having essential permissions to use containers.

We have placed a devcontainer configuration in the `.devcontainer` directory. Install `dev containers` extension in your VSCODE ([extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)).

Open the cloned repository directory folder using VSCODE.

Click on the `Remote Indicator (><)` icon on bottom left and press `Reopen in container` to get started. You will have VSCODE open inside the appropriate development environment with essential plugins including `aws cli` and `terraform cli`.

<!-- TOC --><a name="deployment"></a>
## Deployment

You can simply deploy the cloned repository following the establishment of AWS keys in the development terminal. Alternatively, sBeacon can be used as a module in an existing terraform project.

Do this only once or as you change core libraries or the python lambda layer.

```bash
$ ./init.sh
```

Now set the AWS access keys and token as needed. Since docker uses the same user permissions this may not be needed if you're using an authorised EC2 instance.

```bash
export AWS_ACCESS_KEY_ID="AWS_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="AWS_SECRET_ACCESS_KEY"
export AWS_SESSION_TOKEN="AWS_SESSION_TOKEN"
```

<!-- TOC --><a name="direct-deployment"></a>
### Direct deployment

Install using `terraform init` to pull the module, followed by running `terraform apply` will create the infrastucture. For adding data to the beacon, see the API. To shut down the entire service run `terraform destroy`. Any created datasets will be lost (but not the VCFs on which they are based).

```bash
terraform init
terraform plan # should finish without errors
terraform apply
```

<!-- TOC --><a name="use-as-a-module"></a>
### Use as a module

Your beacon deployment could be a part of a larger program with a front-end and other services. In that case, on the parent folder that the repo folder resides, create a `main.tf` file.

```bash
# main.tf
module "serverless-beacon" {
    # repo folder
    source                      = "./terraform-aws-serverless-beacon"
    beacon-id                   = "au.csiro-serverless.beacon"
    # bucket prefixes
    variants-bucket-prefix      = "sbeacon-"
    metadata-bucket-prefix      = "sbeacon-metadata-"
    lambda-layers-bucket-prefix = "sbeacon-lambda-layers-"
    # beacon variables
    beacon-name                 = ""
    organisation-id             = ""
    organisation-name           = ""
    # aws region
    region                      = "REGION"
}
``` 
Please refer to [./examples/minimum/](./examples/minimum/) or  [./examples/full](./examples/full) to find a minimal and a complete setup. Consider adding `outputs.tf` file as well.

Finally deploy using,

```bash
terraform init
terraform plan # should finish without errors
terraform apply
```

<!-- TOC --><a name="development"></a>
## Development

All the layers needed for the program to run are in layers folder. To add a new layer for immediate use with additional configs, run the following commands. Once the decision to use the library is finalised update the `init.sh` script to automate the process.

* Python layer
```bash
cd terraform-aws-serverless-beacon
pip install --target layers/<Library Name>/python <Library Name>
```

* Binary layer
```bash
# clone the repo somewhere else
git clone <REPO> 
cd <REPO>
mkdir build && cd build && cmake .. && make && make install

# copy the bin and lib folders to a folder inside layers
cp bin terraform-aws-serverless-beacon/layers/<Library Name>/
cp lib terraform-aws-serverless-beacon/layers/<Library Name>/

# troubleshoot with "ldd ./binary-name" to see what libaries needed
# you can use the following command to copy the libraries to binaries/lib/
ldd <binary file> | awk 'NF == 4 { system("cp " $3 " ./layers/binaries/lib") }'
```

* Collaborative development

Please make a copy of `backend.tf.template` with suited parameters and rename as `backend.tf`. Refer to documentation for more information [https://www.terraform.io/language/settings/backends/configuration](https://www.terraform.io/language/settings/backends/configuration). If this is not done, make sure the terraform lock and state files are stored securely to avoid infrastructure-vs-code inconsistencies. Please refer to [./examples/full](./examples/full) to find a an example backend.

<!-- TOC --><a name="api-usage"></a>
## API Usage

<!-- TOC --><a name="example-data"></a>
### Example data

Please find the data in [./examples/test-data/](./examples/test-data/) and use the [./docs/USAGE-GUIDE.md](./docs/USAGE-GUIDE.md) to try the provided test data.

<!-- TOC --><a name="data-ingestion-api"></a>
### Data ingestion API

Please refer to the documentation outlined at [./docs/INGESTION-GUIDE.md](./docs/INGESTION-GUIDE.md).

<!-- TOC --><a name="query-api"></a>
### Query API

Querying is available as per API defined by BeaconV2 [https://beacon-project.io/#the-beacon-v2-model](https://beacon-project.io/#the-beacon-v2-model). 
* All the available endpoints can be retrieved using the deployment url's `/map`. 
* Schema for beacon V2 configuration can be obtained from `/configuration`.
* Entry types are defined at `/entry_types`.

<!-- TOC --><a name="securing-the-api"></a>
## Securing the API

Please refer to the documentation outlined at [./docs/AUTH-GUIDE.md](./docs/AUTH-GUIDE.md).

<!-- TOC --><a name="troubleshooting"></a>
## Troubleshooting

<!-- TOC --><a name="docker-error-invalid-reference-format"></a>
### Docker error (invalid reference format)

This is likely caused by white spaces in your current working directory absolute path. Please use the following command to start images.

```bash
docker run --rm -it -v "`pwd`":"`pwd`" -v /tmp:/tmp  -u `id -u`:`id -g` -w "`pwd`" csiro/sbeacon:latest /bin/bash
```

<!-- TOC --><a name="illegal-instruction-core-dumped"></a>
### Illegal instruction (core dumped)
You'll also need to do this if lambda functions start to display "Error: Runtime exited with error: signal: illegal instruction (core dumped)". In this case it's likely AWS Lambda has moved onto a different architecture from haswell (Family 6, Model 63). You can use cat /proc/cpuinfo in a lambda environment to find the new CPU family and model numbers, or just change -march=haswell to -msse4.2 or -mpopcnt for less optimisation.

```bash
./init.sh -msse4.2 -O3
```

<!-- TOC --><a name="provider-produced-inconsistent-final-plan"></a>
### Provider produced inconsistent final plan

If `terraform apply --auto-approve` complaints about a provider error. Please retry. If the issue persists, please raise an issue with the complete terraform log.

<!-- TOC --><a name="updating-partition_keys-schema-in-gluecatalog_table-according-to-aws-documentation"></a>
### Updating partition_keys schema in glue.catalog_table according to AWS documentation

```bash
Error: error setting partition_keys: Invalid address to set: []string{"partition_keys", "0", "parameters"}
```

This is a known issue as outline in the following PR in terraform AWS.

* https://github.com/hashicorp/terraform-provider-aws/pull/26702

There is not workaround for this yet and we must delete `sbeacon-terms-index` table and `sbeacon-terms` tables before performing a terraform apply. After that, we can do the terraform apply and then run the indexer again.

Issue exists to date and has been active for the last few years - https://github.com/hashicorp/terraform-provider-aws/issues/26686
