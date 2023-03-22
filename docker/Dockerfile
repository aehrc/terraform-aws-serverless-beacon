FROM lambci/lambda:build-python3.8

RUN yum update -y
RUN yum install -y gcc10 gcc10-c++ git openssl-devel libcurl-devel wget bzip2-devel lzma-sdk xz-devel
RUN rm /usr/bin/gcc /usr/bin/g++ /usr/bin/c++
RUN ln -s /usr/bin/gcc10-gcc /usr/bin/gcc
RUN ln -s /usr/bin/gcc10-g++ /usr/bin/g++ 

RUN wget https://www.python.org/ftp/python/3.9.6/Python-3.9.6.tgz 
RUN tar xzf Python-3.9.6.tgz 
RUN cd Python-3.9.6 && ./configure --enable-optimizations && make install
RUN rm /var/lang/bin/python /var/lang/bin/pip
RUN ln /usr/local/bin/python3.9 /var/lang/bin/python
RUN ln /usr/local/bin/pip3.9 /var/lang/bin/pip

RUN wget https://cmake.org/files/v3.20/cmake-3.20.3.tar.gz && \
    tar -xvzf cmake-3.20.3.tar.gz && \
    cd cmake-3.20.3 && \
    ./bootstrap && \
    make && \
    make install

RUN wget https://releases.hashicorp.com/terraform/1.2.8/terraform_1.2.8_linux_386.zip
RUN unzip terraform_1.2.8_linux_386.zip -d /usr/bin/

RUN wget https://archive.apache.org/dist/maven/maven-3/3.5.4/binaries/apache-maven-3.5.4-bin.tar.gz -O /tmp/apache-maven-3.5.4-bin.tar.gz
RUN tar xf /tmp/apache-maven-3.5.4-bin.tar.gz -C /opt
RUN PYTHON=python2 amazon-linux-extras install -y java-openjdk11

ENV M2_HOME="/opt/apache-maven-3.5.4"
ENV PATH="${M2_HOME}/bin:${PATH}"
