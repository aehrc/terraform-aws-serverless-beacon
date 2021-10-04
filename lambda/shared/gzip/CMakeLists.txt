add_compile_options(-march=ivybridge)
# Line above controlled by init.sh
cmake_minimum_required(VERSION 3.5)
set(CMAKE_CXX_STANDARD 17)
project(function LANGUAGES CXX)

add_library (
    Gzip SHARED
    gzip.cpp 
)
set_target_properties(Gzip PROPERTIES
    PUBLIC_HEADER gzip.hpp
)

target_include_directories (Gzip PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

target_compile_options(Gzip PRIVATE
    "-Wall"
    "-Wextra"
    "-Wconversion"
    "-Wshadow"
    "-Wno-sign-conversion"
    "-Werror"
)

target_compile_features(Gzip PRIVATE "cxx_std_17")
