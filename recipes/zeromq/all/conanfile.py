from conans import ConanFile, tools, CMake
from conans.errors import ConanInvalidConfiguration
import os


class ZeroMQConan(ConanFile):
    name = "zeromq"
    version = "4.3.2"
    description = "ZeroMQ is a community of projects focused on decentralized messaging and computing"
    topics = ("conan", "zmq", "libzmq", "message-queue", "asynchronous")
    url = "https://github.com/nemtech/symbol-server-dependencies.git",
    homepage = "https://github.com/zeromq/libzmq"
    license = "LGPL-3.0"
    exports_sources = "CMakeLists.txt"
    generators = "cmake"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False]
    }
    default_options = {
        "shared": True,
        "fPIC": True
    }

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])

        extracted_dir = "libzmq-{}".format(self.version)
        os.rename(extracted_dir, self._source_subfolder)

    def config_options(self):
        if self.settings.os == "Windows":
            if self.settings.compiler == "Visual Studio" and tools.Version(self.settings.compiler.version.value) < 15:
                raise ConanInvalidConfiguration("{} {}, 'Symbol' packages do not support Visual Studio < 15".format(self.name, self.version))

            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            del self.options.fPIC

    def _configure_cmake(self):
        cmake = CMake(self)

        cmake = CMake(self)
        cmake.definitions["ZMQ_BUILD_TESTS"] = False
        cmake.definitions["WITH_PERF_TOOL"] = False
        cmake.definitions["BUILD_SHARED"] = self.options.shared
        cmake.definitions["BUILD_STATIC"] = not self.options.shared
        cmake.definitions["BUILD_TESTS"] = False
        cmake.definitions["ENABLE_CPACK"] = False
        cmake.definitions["WITH_DOCS"] = False
        cmake.definitions["WITH_DOC"] = False
        cmake.configure(build_folder=self._build_subfolder)
        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern="COPYING*", src=self._source_subfolder, dst="licenses")
        cmake = self._configure_cmake()
        cmake.install()

        tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))
        tools.rmdir(os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "ZeroMQ"
        self.cpp_info.names["cmake_find_package_multi"] = "ZeroMQ"

        if self.settings.compiler == "Visual Studio":
            version = "_".join(self.version.split("."))
            if self.settings.build_type == "Debug":
                runtime = "-gd" if self.options.shared else "-sgd"
            else:
                runtime = "" if self.options.shared else "-s"
            library_name = "libzmq-mt%s-%s" % (runtime, version)
            if not os.path.isfile(os.path.join(self.package_folder, "lib", library_name)):
                # unfortunately Visual Studio and Ninja generators produce different file names
                toolset = {"12": "v120",
                           "14": "v140",
                           "15": "v141",
                           "16": "v142"}.get(str(self.settings.compiler.version))
                library_name = "libzmq-%s-mt%s-%s" % (toolset, runtime, version)
            self.cpp_info.libs = [library_name]
        else:
            self.cpp_info.libs = ["zmq"]

        if self.settings.os == "Windows":
            self.cpp_info.system_libs = ["iphlpapi", "ws2_32"]
        elif self.settings.os == "Linux":
            self.cpp_info.system_libs = ["pthread", "rt", "m"]
        if not self.options.shared:
            self.cpp_info.defines.append("ZMQ_STATIC")
