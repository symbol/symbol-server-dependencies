cmake_minimum_required(VERSION 3.14)
project(cmake_wrapper)

if(EXISTS "${CMAKE_BINARY_DIR}/conanbuildinfo.cmake")
  include("${CMAKE_BINARY_DIR}/conanbuildinfo.cmake")
else()
  include(conanbuildinfo.cmake)
endif()

if(${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
	conan_basic_setup(KEEP_RPATHS)
else()
	conan_basic_setup()
endif()

include_directories(${CMAKE_SOURCE_DIR}/source_subfolder/src)
add_subdirectory("source_subfolder")
