cmake_minimum_required(VERSION 3.14)
project(test_package)

set(CMAKE_VERBOSE_MAKEFILE TRUE)

find_package(benchmark 1.8.3 EXACT REQUIRED)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} benchmark::benchmark)
