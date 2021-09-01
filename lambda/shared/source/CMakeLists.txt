
# add_compile_options(-Ofast -march=native)
# Line above controlled by init.sh
cmake_minimum_required(VERSION 3.5)
set(CMAKE_CXX_STANDARD 17)
project(function LANGUAGES CXX)

find_package(aws-lambda-runtime)
find_package(AWSSDK COMPONENTS s3 sns)

add_library (
    Shared SHARED
    awsutils.cpp
#    fastautils.cpp
#    targetutils.cpp
)
target_link_libraries(Shared PRIVATE AWS::aws-lambda-runtime ${AWSSDK_LINK_LIBRARIES})
set_target_properties(Shared PROPERTIES
    PUBLIC_HEADER awsutils.hpp
#    PUBLIC_HEADER fastautils.hpp
#    PUBLIC_HEADER targetutils.hpp
)

target_include_directories (Shared PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

target_compile_options(Shared PRIVATE
    "-Wall"
    "-Wextra"
    "-Wconversion"
    "-Wshadow"
    "-Wno-sign-conversion"
    "-Werror"
)

target_compile_features(Shared PRIVATE "cxx_std_17")
