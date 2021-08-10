# symbol-server-dependencies

Build/Rebuild Conan packages.

Invoke ``scripts/make.sh <recipe|all>``

        It builds the conan packages specified by recipe name (all versions in config.yml file).
        If binaries are already available in ~/.conan/data it exits immediately with success.

Available recipes:
	openssl mongo-c-driver mongo-cxx-driver benchmark zeromq cppzmq milagro rocksdb
