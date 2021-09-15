
# add_compile_options(-Ofast -march=native)
# Line above controlled by init.sh
cmake_minimum_required(VERSION 3.14)
set(CMAKE_CXX_STANDARD 17)
project(function LANGUAGES CXX)

find_package(aws-lambda-runtime)
find_package(AWSSDK COMPONENTS dynamodb s3 sns)

file(GLOB MyCSources *.cpp)
add_executable(${PROJECT_NAME} ${MyCSources})
add_subdirectory(${CMAKE_SOURCE_DIR}/../../shared/source shared)

target_link_libraries(${PROJECT_NAME} PRIVATE 
    Shared
    AWS::aws-lambda-runtime
    ${AWSSDK_LINK_LIBRARIES}
)

target_compile_options(${PROJECT_NAME} PRIVATE
    "-Wall"
    "-Wextra"
    "-Wconversion"
    "-Wshadow"
    "-Wno-sign-conversion")

target_compile_features(${PROJECT_NAME} PRIVATE "cxx_std_17")

aws_lambda_package_target(${PROJECT_NAME} NO_LIBC)
