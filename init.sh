# argument optional, will be passed into add_compile_options()
# e.g ./init.sh '-march=ivybridge'

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


# Build the C++ AWS SDK libraries
cd "${SOURCE}"
# Tag to avoid build error introduced in 1.9.49
git clone https://github.com/aws/aws-sdk-cpp.git --depth=1 --recursive --branch 1.9.48
cd aws-sdk-cpp
sed -i "1s/^/${CMAKE_FIRST_LINE}\n/" CMakeLists.txt
mkdir build
cd build
cmake .. -DBUILD_ONLY="dynamodb;s3;sns" \
  -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_SHARED_LIBS=OFF \
  -DCUSTOM_MEMORY_MANAGEMENT=OFF \
  -DCMAKE_INSTALL_PREFIX=${INCLUDE} \
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
  -DCMAKE_INSTALL_PREFIX=${INCLUDE}
make install
