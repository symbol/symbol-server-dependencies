# symbol-server-dependencies

These are the Conan recipes for [Catapult client](https://github.com/symbol/symbol/tree/fix/update_dependencies_version/client/catapult) dependencies.

## Updating packages

Before building the packages, update each package with the new version.
1. Edit the config.yml file for the package and add the new version
2. Edit the conandata.yml file and add the new package url and checksum. (Note: not every package has a conandata.yml file)
	- Calulate the sha256 hash for the package using ``sha256sum`` tool.

If openssl is updated, set the new version in the mongo-c-driver's ``conanfile.py`` file.

If mongo-c-driver is updated, set the new version in the mongo-cxx-driver ``conanfile.py`` file

## Building

Before you can start building setup the Conan environment.

```sh
conan config init
conan config set general.revisions_enabled=1
conan profile update settings.compiler.libcxx=libstdc++11 default
```

Create the package for the recipe.
This example uses ``benchmark`` recipe and assume you are in the ``recipes`` folder

```sh
cd benchmark/all
conan create . 1.7.0@nemtech/stable
cd -
```

After creating all the packages then upload them.
Here we are uploading the packages to the nemtech remote.

```sh
cd benchmark/all
conan upload benchmark/1.5.3@nemtech/stable -r=nemtech --force
cd -
```

The packages should be created in a specific order, due to dependencies on each other.
* benchmark
* zeromq
* cppzmq
* openssl
* rocksdb
* mongo-c-driver
* mongo-cxx-driver


## Dependencies

- C++ compiler
- [Conan](https://conan.io/)
- [make](https://en.wikipedia.org/wiki/Make_(software))
- [CMake](https://cmake.org/)
- [git](https://git-scm.com/)
