cmake_minimum_required(VERSION 3.10)
project(cim-codebase-generator)

set(CMAKE_CXX_STANDARD 14)

include_directories(cimpp)
include_directories($ENV{GMOCK_HOME}/include)
include_directories($ENV{GTEST_HOME}/include)

add_subdirectory(cimpp)
add_subdirectory(test)
add_subdirectory(googletest)
