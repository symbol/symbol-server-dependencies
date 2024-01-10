## patch, patches ZeroMq cmake, so that it:
##  * checks properly that there's a conan cmake zeromq target
##  * links with libzmq (shared) so that doing find_package(cppzmq) should define libzmq target
##

from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration
import os


class CppZmqConan(ConanFile):
    name = "cppzmq"

    description = "C++ binding for ZeroMQ"
    topics = ("conan", "cppzmq", "zmq-cpp", "zmq", "cpp-bind")
    url = "https://github.com/nemtech/symbol-server-dependencies.git",
    homepage = "https://github.com/zeromq/cppzmq"
    license = "MIT"
    exports_sources = "CMakeLists.txt", "patches/*.patch"
    generators = "cmake", "cmake_find_package"

    settings = "os", "compiler", "build_type", "arch"

    requires = "zeromq/4.3.5@nemtech/stable"

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])

        extracted_dir = "cppzmq-{}".format(self.version)
        os.rename(extracted_dir, self._source_subfolder)

    def config_options(self):
        if self.settings.os == "Windows":
            if self.settings.compiler == "Visual Studio" and tools.Version(self.settings.compiler.version.value) < 15:
                raise ConanInvalidConfiguration("{} {}, 'Symbol' packages do not support Visual Studio < 15".format(self.name, self.version))

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions["CPPZMQ_BUILD_TESTS"] = False
        cmake.configure()
        return cmake

    def _patch_sources(self):
        for patch in self.conan_data["patches"][self.version]:
            tools.patch(**patch)

    def build(self):
        self._patch_sources()
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()

    def package_id(self):
        self.info.header_only()
