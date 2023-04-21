# Serverless Beacon
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

![assets/logo-black.png](assets/logo-black.png)

## Why serverless?
Serverless means the service does not require any servers to be provisioned. The
idea is to minimise running costs, as well as support arbitrary scalablility. It
also means setup is very fast.

## Beacon
The service intends to support beacon v2 according to the
[ga4gh specification](https://github.com/ga4gh-beacon/specification).

## Installation

You can use either local development or a docker environment for development and deployment. First download the repository using the following command. If you're missing the `git` command please have a look at the **Option 1** commands.

```bash
git clone https://github.com/aehrc/terraform-aws-serverless-beacon.git
cd terraform-aws-serverless-beacon
```

### Option 1: Setting up the development environment on Amazon Linux

Skip to next section if you're only interested in deployment or using a different architecture compared to AWS lambda environment. The following setup must be performed on a latest Amazon Linux instance to match the lambda runtimes. If this is not a viable option, please resort to using Docker.

Run the following shell commands to setup necessary build tools. Valid for Amazon Linux development instances.

Required dependencies
* `GCC` and `G++` version `10.3.1 20210422` or later
* `CMake 3.20.3` or later
* Compressionlibraries `xz`, `bzip2` and `zlib`
* Exact python version - `Python3.9`
* OpenJDK version `11.0.18` and Apache Maven `3.5.4`

Install system-wide dependencies

```bash
# Install development essentials
sudo yum update
sudo yum upgrade
sudo yum install -y gcc-c++ git openssl-devel libcurl-devel wget bzip2-devel xz-devel libffi-devel zlib-devel autoconf intltool 
```

Install JAVA and MAVEN
```bash
sudo yum install -y java-11-amazon-corretto-devel
wget https://archive.apache.org/dist/maven/maven-3/3.5.4/binaries/apache-maven-3.5.4-bin.tar.gz -O /tmp/apache-maven-3.5.4-bin.tar.gz
sudo tar xf /tmp/apache-maven-3.5.4-bin.tar.gz -C /opt
rm /tmp/apache-maven-3.5.4-bin.tar.gz

# Run the following commands (or add them to .bashrc and run source ~/.bashrc)
export M2_HOME=/opt/apache-maven-3.5.4
export PATH=${M2_HOME}/bin:${PATH}
```

Install `Python 3.9` to a virtual environment
```bash
# Download and install python
cd ~
wget https://www.python.org/ftp/python/3.9.16/Python-3.9.16.tgz

tar xzf Python-3.9.16.tgz
cd Python-3.9.16 
./configure --enable-optimizations
sudo make altinstall

cd ~
python3.9 -m venv py39

# activate py39 environment
source ~/py39/bin/activate 
```

Install CMake
```bash
# Install CMake
cd ~
wget https://cmake.org/files/v3.20/cmake-3.20.3.tar.gz
tar -xvzf cmake-3.20.3.tar.gz
cd cmake-3.20.3
./bootstrap
make
sudo make install
```

Make sure you have the terraform version `Terraform v1.3.7` or newer if you're not using the docker image. Run the following command to get the terraform binary.

```bash
# only for linux - find other OS version here https://releases.hashicorp.com/terraform/1.3.7/
cd ~
wget https://releases.hashicorp.com/terraform/1.3.7/terraform_1.3.7_linux_386.zip
sudo unzip terraform_1.3.7_linux_386.zip -d /usr/bin/
```

### Option 2: Using the docker image

Initialise the docker container using the following command.

```bash
docker build -t csiro/sbeacon ./docker
```

This will initialise the docker container that contains everything you need including terraform. In order to start the docker container from within the repository directory run the following command.

```bash
docker run --rm -it -v `pwd`:`pwd` -u `id -u`:`id -g` -w `pwd` csiro/sbeacon:latest /bin/bash
```

## Deployment

Once you have configured the development environment or the docker container, install the essential AWS C++ SDKs and initialise the other libraries using the following command. Do this only once or as core C++ libraries change.

```bash
$ ./init.sh -march=haswell -O3
```

You'll also need to do this if lambda functions start to display "Error: Runtime exited with error: signal: illegal instruction (core dumped)". In this case it's likely AWS Lambda has moved onto a different architecture from haswell (Family 6, Model 63). You can use cat /proc/cpuinfo in a lambda environment to find the new CPU family and model numbers, or just change -march=haswell to -msse4.2 or -mpopcnt for less optimisation.

```bash
$ ./init.sh -msse4.2 -O3
```

Now set the AWS access keys and token as needed. Since docker uses the same user permissions this may not be needed if you're using an authorised EC2 instance.

```bash
export AWS_ACCESS_KEY_ID="AWS_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="AWS_SECRET_ACCESS_KEY"
export AWS_SESSION_TOKEN="AWS_SESSION_TOKEN"
```

Install using `terraform init` to pull the module, followed by running `terraform apply` will create the infrastucture. For adding data to the beacon, see the API. To shut down the entire service run `terraform destroy`. Any created datasets will be lost (but not the VCFs on which they are based).

```bash
terraform init
terraform plan # should finish without errors
terraform apply
```

## Use as a module

Your beacon deployment could be a part of a larger program with a front-end and other services. In that case, on the parent folder that the repo folder resides, create a `main.tf` file.
```bash
# main.tf
module "serverless-beacon" {
    # repo folder
    source = "./terraform-aws-serverless-beacon"
    beacon-id = "au.csiro-serverless.beacon"
    # bucket prefixes
    variants-bucket-prefix = "sbeacon-"
    metadata-bucket-prefix = "sbeacon-metadata-"
    lambda-layers-bucket-prefix = "sbeacon-lambda-layers-"
    # beacon variables
    beacon-name = ""
    organisation-id = ""
    organisation-name = ""
    # aws region
    region = "REGION"
}
``` 
Please refer to [./examples](./examples) to find a minimal and a complete setup.
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
<binary file> | awk 'NF == 4 { system("cp " $3 " ./layers/binaries/lib") }'
```

* Collaborative development

Please make a copy of `backend.tf.template` with suited parameters and rename as `backend.tf`. Refer to documentation for more information [https://www.terraform.io/language/settings/backends/configuration](https://www.terraform.io/language/settings/backends/configuration). If this is not done, make sure the terraform lock and state files are stored securely to avoid infrastructure-vs-code inconsistencies. Please refer to [./examples/full](./examples/full) to find a an example backend.

## API

### Data ingestion API

Use the following schemas for data submission

* Submit dataset - please follow the JSON schema at [./shared_resources/schemas/submitDataset-schema-new.json](./shared_resources/schemas/submitDataset-schema-new.json)
* Update dataset - please follow the JSON schema at [./shared_resources/schemas/submitDataset-schema-update.json](./shared_resources/schemas/submitDataset-schema-update.json)

Use the following schemas for submitted entities

* Dataset - [./shared_resources/schemas/dataset-schema.json](./shared_resources/schemas/dataset-schema.json)
* Cohort - [./shared_resources/schemas/cohort-schema.json](./shared_resources/schemas/cohort-schema.json)
* Individual - [./shared_resources/schemas/individual-schema.json](./shared_resources/schemas/individual-schema.json)
* Biosample - [./shared_resources/schemas/biosample-schema.json](./shared_resources/schemas/biosample-schema.json)
* Run - [./shared_resources/schemas/run-schema.json](./shared_resources/schemas/run-schema.json)
* Analysis - [./shared_resources/schemas/analysis-schema.json](./shared_resources/schemas/analysis-schema.json)

### Query API

Querying is available as per API defined by BeaconV2 [https://beacon-project.io/#the-beacon-v2-model](https://beacon-project.io/#the-beacon-v2-model). 
* All the available endpoints can be retrieved using the deployment url's `/map`. 
* Schema for beacon V2 configuration can be obtained from `/configuration`.
* Entry types are defined at `/entry_types`.
