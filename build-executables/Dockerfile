FROM lambci/lambda:build-python3.6

ENV AWS_DEFAULT_REGION ap-southeast-2

RUN yum update

RUN mkdir shared_resources

RUN git clone --depth 1 --branch develop https://github.com/samtools/htslib.git
RUN cd htslib && autoreconf && ./configure --enable-libcurl && make
RUN cp htslib/tabix shared_resources/

RUN git clone --depth 1 --branch develop https://github.com/samtools/bcftools.git
RUN cd bcftools && autoreconf && ./configure && make
RUN cp bcftools/bcftools shared_resources/
