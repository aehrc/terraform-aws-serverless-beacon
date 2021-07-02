ABSOLUTE_PATH="${PWD}/${2}"
mkdir -p "${1}/../build"
cd "${1}/../build"
cmake "${1}" -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="${PWD}/../../../libraries/include"
make aws-lambda-package-function
mv "${1}/../build/function.zip" "${ABSOLUTE_PATH}"
