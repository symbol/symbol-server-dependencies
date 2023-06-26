## Note: the package always contains both libraries (shared vs static) independent of shared setting
## that is done to avoid patching CMakefile

from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration
import os
import glob
import shutil

class RocksDB(ConanFile):
    name = "rocksdb"
    description = "A library that provides an embeddable, persistent key-value store for fast storage"
    topics = ("conan", "rocksdb", "database", "leveldb", "facebook", "key-value")
    homepage = "https://github.com/facebook/rocksdb"
    url = "https://github.com/nemtech/symbol-server-dependencies.git",
    license = ("GPL-2.0-only", "Apache-2.0")
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake", "cmake_find_package"

    settings = "os", "compiler", "build_type", "arch"

    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "enable_sse": [False, "sse42", "avx2"],

        "use_rtti": [True, False],
        "with_gflags": [True, False],
        "with_jemalloc": [True, False],
        "with_lz4": [True, False],
        "with_snappy": [True, False],
        "with_tbb": [True, False],
        "with_zlib": [True, False],
        "with_zstd": [True, False]
    }
    default_options = {
        "shared": True,
        "fPIC": True,
        "enable_sse": "sse42",

        "use_rtti": True,
        "with_gflags": False,
        "with_jemalloc": False,
        "with_lz4": False,
        "with_snappy": False,
        "with_tbb": False,
        "with_zlib": False,
        "with_zstd": False
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
        if self.settings.build_type == "Debug":
            self.options.use_rtti = True  # Rtti are used in asserts for debug mode...

    def _configure_cmake(self):
        cmake = CMake(self)

        cmake.definitions["FAIL_ON_WARNINGS"] = False
        cmake.definitions["WITH_TESTS"] = False
        cmake.definitions["WITH_TOOLS"] = False
        cmake.definitions["WITH_CORE_TOOLS"] = False
        cmake.definitions["WITH_BENCHMARK_TOOLS"] = False
        cmake.definitions["WITH_FOLLY_DISTRIBUTED_MUTEX"] = False
        cmake.definitions["WITH_MD_LIBRARY"] = self.settings.compiler == "Visual Studio" and "MD" in self.settings.compiler.runtime
        cmake.definitions["ROCKSDB_INSTALL_ON_WINDOWS"] = self.settings.os == "Windows"
        cmake.definitions["WITH_GFLAGS"] = self.options.with_gflags
        cmake.definitions["WITH_SNAPPY"] = self.options.with_snappy
        cmake.definitions["WITH_LZ4"] = self.options.with_lz4
        cmake.definitions["WITH_ZLIB"] = self.options.with_zlib
        cmake.definitions["WITH_ZSTD"] = self.options.with_zstd
        cmake.definitions["WITH_TBB"] = self.options.with_tbb
        cmake.definitions["WITH_JEMALLOC"] = self.options.with_jemalloc
        cmake.definitions["ROCKSDB_BUILD_SHARED"] = self.options.shared
        #cmake.definitions["ROCKSDB_LIBRARY_EXPORTS"] = self.settings.os == "Windows" and self.options.shared
        #cmake.definitions["ROCKSDB_DLL" ] = self.settings.os == "Windows" and self.options.shared

        cmake.definitions["USE_RTTI"] = self.options.use_rtti
        if "arm" in str(self.settings.arch):
            self.options.enable_sse = "False"

        if self.options.enable_sse == "False":
          cmake.definitions["PORTABLE"] = True
          cmake.definitions["FORCE_SSE42"] = False
        elif self.options.enable_sse == "sse42":
          cmake.definitions["PORTABLE"] = True
          cmake.definitions["FORCE_SSE42"] = True
        elif self.options.enable_sse == "avx2":
          cmake.definitions["PORTABLE"] = False
          cmake.definitions["FORCE_SSE42"] = False

        cmake.definitions["WITH_NUMA"] = False

        cmake.configure(build_folder=self._build_subfolder)
        return cmake

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = "{name}-{version}".format(
          name = self.name,
          version = self.version
        )
        os.rename(extracted_dir, self._source_subfolder)

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def requirements(self):
        if self.options.with_gflags:
            self.requires("gflags/2.2.2")
        if self.options.with_snappy:
            self.requires("snappy/1.1.7")
        if self.options.with_lz4:
            self.requires("lz4/1.9.2")
        if self.options.with_zlib:
            self.requires("zlib/1.2.11")
        if self.options.with_zstd:
            self.requires("zstd/1.3.8")
        if self.options.with_tbb:
            self.requires("tbb/2019_u9")
        if self.options.with_jemalloc:
            self.requires("jemalloc/5.2.1")

    def _remove_static_libraries(self):
        for static_lib_name in ["lib*.a", "{}.lib".format(self.name)]:
            for file in glob.glob(os.path.join(self.package_folder, "lib", static_lib_name)):
                os.remove(file)

    def package(self):
        self.copy("COPYING", dst="licenses", src=self._source_subfolder)
        self.copy("LICENSE*", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()
        #if self.options.shared:
        #    self._remove_static_libraries()

        #tools.rmdir(os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "RocksDB"
        self.cpp_info.names["cmake_find_package_multi"] = "RocksDB"
        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == "Windows":
            self.cpp_info.system_libs = ["Shlwapi.lib", "Rpcrt4.lib"]
            if self.options.shared:
                self.cpp_info.defines = ["ROCKSDB_DLL"]
        elif self.settings.os == "Linux":
            self.cpp_info.system_libs = ["pthread", "m"]
