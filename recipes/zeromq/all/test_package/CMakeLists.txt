cmake_minimum_required(VERSION 3.14)
project(test_package)

set(CMAKE_VERBOSE_MAKEFILE TRUE)

find_package(ZeroMQ REQUIRED)

message("zeromq    ver: ${ZeroMQ_VERSION}")
message("zeromq    inc: ${ZeroMQ_INCLUDE_DIR}")
message("zeromq    lib: ${ZeroMQ_LIBRARY}")

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} ZeroMQ::ZeroMQ)
