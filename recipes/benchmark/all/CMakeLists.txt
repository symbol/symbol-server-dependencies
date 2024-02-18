cmake_minimum_required(VERSION 3.14)
project(cmake_wrapper)

#if(EXISTS "${CMAKE_BINARY_DIR}/conanbuildinfo.cmake")
#  include("${CMAKE_BINARY_DIR}/conanbuildinfo.cmake")
#else()
#  include(conanbuildinfo.cmake)
#endif()

if (APPLE)
    set(CMAKE_INSTALL_RPATH "@executable_path/../lib")
else()
    set(CMAKE_INSTALL_RPATH "$ORIGIN/../lib")
endif()

set(CMAKE_BUILD_WITH_INSTALL_RPATH ON)

add_subdirectory(".")
