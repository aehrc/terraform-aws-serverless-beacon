#!/usr/bin/bash
# argument optional, will be passed into add_compile_options()
# e.g ./init.sh '-march=ivybridge'

# 
# Housekeeping and cleanups
# 

set -ex
REPOSITORY_DIRECTORY="${PWD}"
LIBRARIES="${REPOSITORY_DIRECTORY}/libraries"
SOURCE="${LIBRARIES}/source"
INCLUDE="${LIBRARIES}/include"

if [ -z "$1" ]
  then
    CMAKE_FIRST_LINE=""
  else
    CMAKE_FIRST_LINE="add_compile_options(${@})"
fi

# Update CMakeLists.txt for each C++ lambda function
for cmakefile in "${REPOSITORY_DIRECTORY}/lambda/"*/source/CMakeLists.txt; do
  sed -i "1s/^.*/${CMAKE_FIRST_LINE}/" "${cmakefile}"
done

# Clean ~/varscot-libraries
if [ -d "${LIBRARIES}" ]
  then
    rm -rf "${LIBRARIES}"
fi

mkdir "${LIBRARIES}"
mkdir "${INCLUDE}"
mkdir "${SOURCE}"

# 
# Runtime libraries for CPP development
# 

# Build the C++ AWS SDK libraries
cd "${SOURCE}"
# Tag to avoid build error introduced in 1.9.49
git clone https://github.com/aws/aws-sdk-cpp.git --depth=1 --recursive --branch 1.11.63
cd aws-sdk-cpp
sed -i "1s/^/${CMAKE_FIRST_LINE}\n/" CMakeLists.txt
mkdir build
cd build
cmake .. -DBUILD_ONLY="dynamodb;s3;sns" \
  -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_SHARED_LIBS=OFF \
  -DCUSTOM_MEMORY_MANAGEMENT=OFF \
  -DCMAKE_INSTALL_PREFIX="${INCLUDE}" \
  -DENABLE_UNITY_BUILD=ON
make install

# Build the lambda runtime libraries
cd ${SOURCE}
git clone https://github.com/awslabs/aws-lambda-cpp-runtime.git --depth=1
cd aws-lambda-cpp-runtime
sed -i "1s/^/${CMAKE_FIRST_LINE}\n/" CMakeLists.txt
mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_SHARED_LIBS=OFF \
  -DCMAKE_INSTALL_PREFIX="${INCLUDE}"
make install

#
# building lambda layers
#

# tabix
cd ${SOURCE}
git clone --recursive --depth 1 --branch develop https://github.com/samtools/htslib.git 
cd htslib && autoreconf && ./configure --enable-libcurl && make
cd ${REPOSITORY_DIRECTORY}
mkdir -p layers/binaries/lib
mkdir -p layers/binaries/bin
ldd ${SOURCE}/htslib/tabix | awk 'NF == 4 { system("cp " $3 " ./layers/binaries/lib") }'
cp ${SOURCE}/htslib/tabix ./layers/binaries/bin/

# bcftools
cd ${SOURCE}
git clone --recursive --depth 1 --branch develop https://github.com/samtools/bcftools.git
cd bcftools && autoreconf && ./configure && make
cd ${REPOSITORY_DIRECTORY}
mkdir -p layers/binaries/lib
mkdir -p layers/binaries/bin
ldd ${SOURCE}/bcftools | awk 'NF == 4 { system("cp " $3 " ./layers/binaries/lib") }'
cp ${SOURCE}/bcftools/bcftools ./layers/binaries/bin/

# python libraries layer
cd ${REPOSITORY_DIRECTORY}
pip install jsons==1.6.3 --target layers/python_libraries/python
pip install jsonschema==4.18.0 --target layers/python_libraries/python
pip install pydantic==2.0.2 --target layers/python_libraries/python
pip install pyhumps==3.8.0 --target layers/python_libraries/python
pip install pynamodb==5.5.0 --target layers/python_libraries/python
pip install pyorc==0.8.0 --target layers/python_libraries/python
pip install requests==2.31.0 --target layers/python_libraries/python
pip install smart_open==6.3.0 --target layers/python_libraries/python
pip install strenum==0.4.15 --target layers/python_libraries/python
