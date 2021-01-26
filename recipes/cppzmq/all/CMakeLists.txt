cmake_minimum_required(VERSION 3.13)
project(cmake_wrapper)

include(conanbuildinfo.cmake)
if(${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
	conan_basic_setup(KEEP_RPATHS)
else()
	conan_basic_setup()
endif()

add_subdirectory(source_subfolder)
