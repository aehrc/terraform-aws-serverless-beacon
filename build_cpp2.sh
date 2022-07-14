mkdir -p "${1}/build"
cd "${1}/build"
cmake "../source" -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="${PWD}/../../../libraries/include"
make aws-lambda-package-function
unzip  function.zip -d function_binaries
rm function.zip
