## Note: the package always contains both libraries (shared vs static) independent of shared setting
## that is done to avoid patching CMakefile

from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration
import os
import glob
import shutil

class ApacheMilagro(ConanFile):
    name = "milagro"
    description = "Milagro is core security infrastructure and crypto libraries for decentralized networks and distributed systems."
    topics = ("conan", "milagro", "cryptography")
    homepage = "https://github.com/apache/incubator-milagro-crypto-c"
    url = "https://github.com/nemtech/symbol-server-dependencies.git"
    license = ("Apache-2.0")
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake" #, "cmake_find_package"

    settings = "os", "compiler", "build_type", "arch"

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
    
    def config_options(self):
        if self.settings.os == "Windows":
            if self.settings.compiler == "Visual Studio" and tools.Version(self.settings.compiler.version.value) < 15:
                raise ConanInvalidConfiguration("{} {}, 'Symbol' packages do not support Visual Studio < 15".format(self.name, self.version))

            del self.options.fPIC

        minimal_cpp_standard = "11"
        if self.settings.compiler.cppstd:
            tools.check_min_cppstd(self, minimal_cpp_standard)

    def configure(self):
        if self.settings.arch not in ["x86_64"]:
            raise ConanInvalidConfiguration("'Symbol' packages support only x64 arch")

    def _configure_cmake(self):
        cmake = CMake(self)

        cmake.definitions["BUILD_TESTING"] = False
        cmake.definitions["BUILD_PYTHON"] = False
        cmake.definitions["BUILD_EXAMPLES"] = False
        cmake.definitions["BUILD_BENCHMARKS"] = False
        cmake.definitions["BUILD_DOCS"] = False

        cmake.configure(build_folder=self._build_subfolder)
        return cmake

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = "incubator-milagro-crypto-c-{version}".format(version = self.version)
        os.rename(extracted_dir, self._source_subfolder)

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy("COPYING", dst="licenses", src=self._source_subfolder)
        self.copy("LICENSE*", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "AMCL"
        self.cpp_info.names["cmake_find_package_multi"] = "AMCL"
        self.cpp_info.libs = tools.collect_libs(self)
       
