# symbol-server-dependencies

These are the Conan recipes for [Catapult client](https://github.com/symbol/symbol/tree/main/client/catapult) dependencies.

## Updating packages

Before building the packages, update each package with the new version.
1. Edit the config.yml file for the package and add the new version
2. Edit the conandata.yml file and add the new package url and checksum. (Note: not every package has a conandata.yml file)
	- Calculate the sha256 hash for the package using ``sha256sum`` tool.

If openssl is updated, set the new version in the mongo-c-driver's ``conanfile.py`` file.

If mongo-c-driver is updated, set the new version in the mongo-cxx-driver ``conanfile.py`` file.

## Building

Before you can start building, set up the Conan environment.

```sh
conan profile detect --name default
conan remote add nemtech https://conan.symbol.dev/artifactory/api/conan/catapult
```

Create the package for the recipe.
This example uses ``benchmark`` recipe and assumes you are in the ``recipes`` folder

```sh
cd benchmark/all
conan create --name benchmark --version 1.8.3 --user nemtech --channel stable .
cd -
```

After creating all the packages then upload them.
Here we are uploading the packages to the nemtech remote.

```sh
cd benchmark/all
conan upload benchmark/1.8.3@nemtech/stable -r=nemtech --force
cd -
```

The packages should be created in a specific order, due to dependencies on each other.
* benchmark
* zeromq
* cppzmq
* rocksdb
* mongo-c-driver
* mongo-cxx-driver

## Dependencies

- C++ compiler
- [Conan](https://conan.io/)
- [make](https://en.wikipedia.org/wiki/Make_(software))
- [CMake](https://cmake.org/)
- [git](https://git-scm.com/)

There are several reasons why custom Conan packages were created for Catapult client.
1. The main reason was to add support rpath in Darwin OS.
2. Benchmark was updated to prevent benchmark from actually removing cmake files.
3. Mongo-c has specific changes for Visual Studio and fix the ENABLE_AUTOMATIC_INIT_AND_CLEANUP.
4. Mongo-cxx has some customization for Visual Studio plus it was copying files instead of using cmake.install() in conanfile.
5. ZeroMQ has rpath support added.
6. Cppzmq has cmakelist file which was incorrect and this was fix.
7. RocksDB has rpath support added.
