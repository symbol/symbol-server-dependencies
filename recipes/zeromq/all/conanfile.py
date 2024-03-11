from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rmdir
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version
import os


class ZeroMQConan(ConanFile):
    name = "zeromq"
    description = "ZeroMQ is a community of projects focused on decentralized messaging and computing"
    topics = ("conan", "zmq", "libzmq", "message-queue", "asynchronous")
    url = "https://github.com/symbol/symbol-server-dependencies.git",
    homepage = "https://github.com/zeromq/libzmq"
    license = "LGPL-3.0"
    package_type = "library"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False]
    }
    default_options = {
        "shared": True,
        "fPIC": True
    }

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def config_options(self):
        if self.settings.os == "Windows":
            if self.settings.compiler == "Visual Studio" and Version(self.settings.compiler.version.value) < 15:
                raise ConanInvalidConfiguration("{} {}, 'Symbol' packages do not support Visual Studio < 15".format(self.name, self.version))

            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            del self.options.fPIC

    def layout(self):
        cmake_layout(self, src_folder="src")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["ZMQ_BUILD_TESTS"] = False
        tc.cache_variables["WITH_PERF_TOOL"] = False
        tc.cache_variables["BUILD_SHARED"] = self.options.shared
        tc.cache_variables["BUILD_STATIC"] = not self.options.shared
        tc.cache_variables["BUILD_TESTS"] = False
        tc.cache_variables["ENABLE_CPACK"] = False
        tc.cache_variables["WITH_DOCS"] = False
        tc.cache_variables["WITH_DOC"] = False

        if "Macos" == self.settings.os:
            tc.blocks["rpath"].skip_rpath = False

        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="COPYING*", src=self.source_folder, dst="licenses")
        cmake = CMake(self)
        cmake.install()

        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "ZeroMQ")
        self.cpp_info.set_property("cmake_target_name", "ZeroMQ::ZeroMQ")
        self.cpp_info.set_property("pkg_config_name", "ZeroMQ")

        if is_msvc(self):
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
