cmake_minimum_required(VERSION 3.13)
project(test_package)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

find_package(cppzmq REQUIRED)

message("zeromq    inc: ${ZeroMQ_INCLUDE_DIR}")
message("zeromq    lib: ${ZeroMQ_LIBRARY}")
message("cppzmq    inc: ${cppzmq_INCLUDE_DIR}")

include_directories(SYSTEM ${ZeroMQ_INCLUDE_DIR})
include_directories(SYSTEM ${cppzmq_INCLUDE_DIR})

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} ZeroMQ::ZeroMQ)
