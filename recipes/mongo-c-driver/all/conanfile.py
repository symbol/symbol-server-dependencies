from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration
import os


class MongoCDriverConan(ConanFile):
    name = "mongo-c-driver"
    version = "1.17.0"
    description = "A high-performance MongoDB driver for C"
    topics = ("conan", "mongoc", "libmongoc", "mongodb")
    url = "https://github.com/nemtech/symbol-server-dependencies.git",
    homepage = "https://github.com/mongodb/mongo-c-driver"
    license = "Apache-2.0"
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"

    settings = "arch", "build_type", "compiler", "os"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "enable_automatic_init_and_cleanup": [True, False]
    }
    default_options = {"shared": True, "fPIC": True, "enable_automatic_init_and_cleanup": False}

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])

        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def config_options(self):
        if self.settings.os == "Windows":
            if self.settings.compiler == "Visual Studio" and tools.Version(self.settings.compiler.version.value) < 15:
                raise ConanInvalidConfiguration("{} {}, 'Symbol' packages do not support Visual Studio < 15".format(self.name, self.version))

            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def _configure_cmake(self):
        cmake = CMake(self)

        cmake.definitions["ENABLE_TESTS"] = "OFF"
        cmake.definitions["ENABLE_EXAMPLES"] = "OFF"
        cmake.definitions["ENABLE_AUTOMATIC_INIT_AND_CLEANUP"] = "OFF" if self.options.enable_automatic_init_and_cleanup else "ON"
        cmake.definitions["ENABLE_BSON"] = "ON"
        cmake.definitions["ENABLE_SASL"] = "OFF"
        cmake.definitions["ENABLE_STATIC"] = "OFF" if self.options.shared else "ON"
        cmake.definitions["ENABLE_SHM_COUNTERS"] = "OFF"
        cmake.definitions["ENABLE_SNAPPY"] = "OFF"
        cmake.definitions["ENABLE_SRV"] = "OFF"
        cmake.definitions["ENABLE_ZLIB"] = "OFF"
        cmake.definitions["ENABLE_ZSTD"] = "OFF"

        if tools.os_info.is_linux:
            cmake.definitions["CMAKE_SHARED_LINKER_FLAGS"] = "-ldl"
            cmake.definitions["CMAKE_EXE_LINKER_FLAGS"] = "-ldl"

        if self.settings.compiler == "Visual Studio":
            cmake.definitions["ENABLE_EXTRA_ALIGNMENT"] = "OFF"

        cmake.configure(build_folder=self._build_subfolder)
        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern="COPYING*", dst="licenses", src=self._source_subfolder)
        self.copy("Find*.cmake", ".", ".")

        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        if self.options.shared:
            self.cpp_info.libs = ['mongoc-1.0', 'bson-1.0']
        else:
            self.cpp_info.libs = ['mongoc-static-1.0', 'bson-static-1.0']

        self.cpp_info.includedirs = [os.path.join("include", "libmongoc-1.0"), os.path.join("include", "libbson-1.0")]

        if tools.os_info.is_macos:
            self.cpp_info.frameworks.extend(['CoreFoundation', 'Security'])

        if tools.os_info.is_linux:
            self.cpp_info.system_libs.extend(["rt", "pthread", "dl"])

        if not self.options.shared:
            self.cpp_info.defines.extend(['BSON_STATIC=1', 'MONGOC_STATIC=1'])

            if tools.os_info.is_linux or tools.os_info.is_macos:
                self.cpp_info.system_libs.append('resolv')

            if tools.os_info.is_windows:
                self.cpp_info.system_libs.extend(['ws2_32.lib', 'secur32.lib', 'crypt32.lib', 'BCrypt.lib', 'Dnsapi.lib'])
