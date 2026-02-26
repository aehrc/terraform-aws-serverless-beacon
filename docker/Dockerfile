FROM --platform=x86_64 public.ecr.aws/sam/build-python3.12:latest-x86_64

RUN dnf update -y
RUN dnf install -y git tar make openssl-devel libcurl-devel wget bzip2-devel xz-devel libffi-devel zlib-devel autoconf intltool 
RUN dnf install -y gcc gcc-c++ cmake

RUN wget https://releases.hashicorp.com/terraform/1.12.2/terraform_1.12.2_linux_amd64.zip
RUN unzip terraform_1.12.2_linux_amd64.zip -d /usr/bin/

# Copy requirements.txt
RUN pip install --upgrade pip
COPY requirements.txt ./
RUN pip install -r requirements.txt

# docker cli
RUN wget https://download.docker.com/linux/static/stable/x86_64/docker-29.1.3.tgz -qO- | tar xvfz - docker/docker --strip-components=1
RUN cp -rp ./docker /usr/local/bin/ && rm -r ./docker

RUN dnf install -y maven