cmake_minimum_required(VERSION 3.14)
project(test_package)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

find_package(libmongoc-1.0 REQUIRED)
find_package(libbson-1.0 REQUIRED)
find_package(ZLIB REQUIRED)

message ("--   mongoc found version \"${MONGOC_VERSION}\"")
message ("--   mongoc include path \"${MONGOC_INCLUDE_DIRS}\"")
message ("--   mongoc libraries \"${MONGOC_LIBRARIES}\"")
message ("--   zlib libraries \"${ZLIB_LIBRARIES}\"")

include_directories(SYSTEM ${MONGOC_INCLUDE_DIRS} ${ZLIB_INCLUDE_DIRS})
add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} ${MONGOC_LIBRARIES} ${ZLIB_LIBRARIES})
