cmake_minimum_required(VERSION 3.14)
project(test_package)

find_package(libmongoc-1.0 REQUIRED)
find_package(libbson-1.0 REQUIRED)
find_package(ZLIB REQUIRED)

message ("--   mongoc found version \"${MONGOC_VERSION}\"")
message ("--   mongoc include path \"${mongoc-1.0_INCLUDE_DIRS}\"")
message ("--   mongoc libraries \"${mongoc-1.0_LIBRARIES}\"")
message ("--   zlib libraries \"${ZLIB_LIBRARIES}\"")

include_directories(SYSTEM ${mongoc-1.0_INCLUDE_DIRS} ${ZLIB_INCLUDE_DIRS})
add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} ${mongoc-1.0_LIBRARIES} ${ZLIB_LIBRARIES})
