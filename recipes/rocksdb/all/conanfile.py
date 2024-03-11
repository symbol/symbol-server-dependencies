## Note: the package always contains both libraries (shared vs static) independent of shared setting
## that is done to avoid patching CMakefile

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, collect_libs, get
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version
from conan.errors import ConanInvalidConfiguration
import os
import glob

class RocksDB(ConanFile):
    name = "rocksdb"
    description = "A library that provides an embeddable, persistent key-value store for fast storage"
    topics = ("conan", "rocksdb", "database", "leveldb", "facebook", "key-value")
    homepage = "https://github.com/facebook/rocksdb"
    url = "https://github.com/nemtech/symbol-server-dependencies.git",
    license = ("GPL-2.0-only", "Apache-2.0")
    package_type = "library"

    settings = "os", "compiler", "build_type", "arch"

    options = {
        "shared": [True, False],
        "fPIC": [True, False],

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

        "use_rtti": True,
        "with_gflags": False,
        "with_jemalloc": False,
        "with_lz4": False,
        "with_snappy": False,
        "with_tbb": False,
        "with_zlib": False,
        "with_zstd": False
    }

    
    def config_options(self):
        if self.settings.os == "Windows":
            if self.settings.compiler == "Visual Studio" and Version(self.settings.compiler.version.value) < 15:
                raise ConanInvalidConfiguration("{} {}, 'Symbol' packages do not support Visual Studio < 15".format(self.name, self.version))

            del self.options.fPIC

        minimal_cpp_standard = "11"
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, minimal_cpp_standard)

    def configure(self):
        if self.settings.build_type == "Debug":
            self.options.use_rtti = True  # Rtti are used in asserts for debug mode...

    def generate(self):
        tc = CMakeToolchain(self)

        tc.cache_variables["FAIL_ON_WARNINGS"] = False
        tc.cache_variables["WITH_TESTS"] = False
        tc.cache_variables["WITH_TOOLS"] = False
        tc.cache_variables["WITH_CORE_TOOLS"] = False
        tc.cache_variables["WITH_BENCHMARK_TOOLS"] = False
        tc.cache_variables["WITH_FOLLY_DISTRIBUTED_MUTEX"] = False
        tc.cache_variables["WITH_MD_LIBRARY"] = is_msvc(self) and "MD" in self.settings.compiler.runtime
        tc.cache_variables["ROCKSDB_INSTALL_ON_WINDOWS"] = self.settings.os == "Windows"
        tc.cache_variables["WITH_GFLAGS"] = self.options.with_gflags
        tc.cache_variables["WITH_SNAPPY"] = self.options.with_snappy
        tc.cache_variables["WITH_LZ4"] = self.options.with_lz4
        tc.cache_variables["WITH_ZLIB"] = self.options.with_zlib
        tc.cache_variables["WITH_ZSTD"] = self.options.with_zstd
        tc.cache_variables["WITH_TBB"] = self.options.with_tbb
        tc.cache_variables["WITH_JEMALLOC"] = self.options.with_jemalloc
        tc.cache_variables["ROCKSDB_BUILD_SHARED"] = self.options.shared

        tc.cache_variables["USE_RTTI"] = self.options.use_rtti

        # sse was removed https://github.com/facebook/rocksdb/pull/11419
        tc.cache_variables["PORTABLE"] = "TRUE"
        tc.cache_variables["WITH_NUMA"] = False

        if "Macos" == self.settings.os:
            tc.blocks["rpath"].skip_rpath = False

        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def requirements(self):
        if self.options.with_gflags:
            self.requires("gflags/2.2.2")
        if self.options.with_snappy:
            self.requires("snappy/1.1.10")
        if self.options.with_lz4:
            self.requires("lz4/1.9.4")
        if self.options.with_zlib:
            self.requires("zlib/[>=1.2.11 <2]")
        if self.options.with_zstd:
            self.requires("zstd/1.5.5")
        if self.options.get_safe("with_tbb"):
            self.requires("onetbb/2021.10.0")
        if self.options.with_jemalloc:
            self.requires("jemalloc/5.3.0")

    def _remove_static_libraries(self):
        for static_lib_name in ["lib*.a", "{}.lib".format(self.name)]:
            for file in glob.glob(os.path.join(self.package_folder, "lib", static_lib_name)):
                os.remove(file)

    def package(self):
        copy(self, "COPYING", dst="licenses", src=self.source_folder)
        copy(self, "LICENSE*", dst="licenses", src=self.source_folder)
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        cmake_target = "rocksdb-shared" if self.options.shared else "rocksdb"
        self.cpp_info.set_property("cmake_find_package", "RocksDB")
        self.cpp_info.set_property("cmake_target_name", f"RocksDB::{cmake_target}")
        self.cpp_info.libs = collect_libs(self)
        if self.settings.os == "Windows":
            self.cpp_info.system_libs = ["Shlwapi.lib", "Rpcrt4.lib"]
            if self.options.shared:
                self.cpp_info.defines = ["ROCKSDB_DLL"]
        elif self.settings.os == "Linux":
            self.cpp_info.system_libs = ["pthread", "m"]
