cmake_minimum_required(VERSION 3.13)
project(test_package)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

find_package(AMCL REQUIRED)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} AMCL::AMCL)

message("--    amcl dirs \"${AMCL_INCLUDE_DIRS}\"")
message("--    amcl includes \"${AMCL_INCLUDES}\"")
message("--    amcl version \"${AMCL_VERSION}\"")

