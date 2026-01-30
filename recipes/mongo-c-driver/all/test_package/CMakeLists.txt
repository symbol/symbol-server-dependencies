cmake_minimum_required(VERSION 3.14)
project(test_package)

find_package(mongoc REQUIRED)

message ("--   mongoc found version \"${mongoc_VERSION}\"")
message ("--   mongoc include path \"${mongoc_INCLUDE_DIRS}\"")
message ("--   mongoc libraries \"${mongoc_LIBRARIES}\"")

include_directories(SYSTEM ${mongoc_INCLUDE_DIRS} ${ZLIB_INCLUDE_DIRS})
add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} ${mongoc_LIBRARIES} ${ZLIB_LIBRARIES})
