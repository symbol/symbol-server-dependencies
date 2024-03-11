from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version
import os


class MongoCDriverConan(ConanFile):
	name = "mongo-c-driver"
	description = "A high-performance MongoDB driver for C"
	topics = ("conan", "mongoc", "libmongoc", "mongodb")
	url = "https://github.com/symbol/symbol-server-dependencies",
	homepage = "https://github.com/mongodb/mongo-c-driver"
	license = "Apache-2.0"
	short_paths = True
	package_type = "library"

	settings = "arch", "build_type", "compiler", "os"
	options = {
		"shared": [True, False],
		"fPIC": [True, False],
		"enable_automatic_init_and_cleanup": [True, False]
	}
	default_options = {"shared": True, "fPIC": True, "enable_automatic_init_and_cleanup": False}

	def requirements(self):
		if self.settings.os == "Linux":
			self.requires("openssl/3.2.1")

	def layout(self):
		cmake_layout(self, src_folder="src")

	def source(self):
		get(self, **self.conan_data["sources"][self.version], strip_root=True)

	def config_options(self):
		if self.settings.os == "Windows":
			if is_msvc(self) and Version(self.settings.compiler.version.value) < 15:
				raise ConanInvalidConfiguration("{} {}, 'Symbol' packages do not support Visual Studio < 15".format(self.name, self.version))

			del self.options.fPIC

	def configure(self):
		del self.settings.compiler.libcxx
		del self.settings.compiler.cppstd

	def generate(self):
		tc = CMakeToolchain(self)

		tc.cache_variables["ENABLE_TESTS"] = "OFF"
		tc.cache_variables["ENABLE_EXAMPLES"] = "OFF"
		tc.cache_variables["ENABLE_AUTOMATIC_INIT_AND_CLEANUP"] = "ON" if self.options.enable_automatic_init_and_cleanup else "OFF"
		tc.cache_variables["ENABLE_BSON"] = "ON"
		tc.cache_variables["ENABLE_SASL"] = "OFF"
		tc.cache_variables["ENABLE_STATIC"] = "OFF" if self.options.shared else "ON"
		tc.cache_variables["ENABLE_SHM_COUNTERS"] = "OFF"
		tc.cache_variables["ENABLE_SNAPPY"] = "OFF"
		tc.cache_variables["ENABLE_SRV"] = "OFF"
		tc.cache_variables["ENABLE_ZLIB"] = "OFF"
		tc.cache_variables["ENABLE_ZSTD"] = "OFF"
		tc.cache_variables["ENABLE_MONGODB_AWS_AUTH"] = "OFF"

		if "Linux" == self.settings.os:
			tc.cache_variables["CMAKE_SHARED_LINKER_FLAGS"] = "-ldl"
			tc.cache_variables["CMAKE_EXE_LINKER_FLAGS"] = "-ldl"

		if is_msvc(self):
			tc.cache_variables["ENABLE_EXTRA_ALIGNMENT"] = "OFF"

		if Version(self.version) >= "1.25.0":
			tc.cache_variables["BUILD_VERSION"] = str(self.version)

		if "Macos" == self.settings.os:
			tc.blocks["rpath"].skip_rpath = False

		tc.generate()
		deps = CMakeDeps(self)
		deps.generate()

	def build(self):
		cmake = CMake(self)
		cmake.configure()
		cmake.build()

	def package(self):
		copy(self, pattern="COPYING*", dst="licenses", src=self.source_folder)
		cmake = CMake(self)
		cmake.install()

	@property
	def _module_subfolder(self):
		return os.path.join("lib", "cmake")

	@property
	def _module_file_rel_path(self):
		return os.path.join(self._module_subfolder, f"conan-official-{self.name}-variables.cmake")

	def package_info(self):
		mongoc_target = "mongoc_shared" if self.options.shared else "mongoc_static"
		self.cpp_info.set_property("cmake_file_name", "mongoc-1.0")
		self.cpp_info.set_property("cmake_target_name", f"mongo::{mongoc_target}")

		# mongoc
		self.cpp_info.components["mongoc"].set_property("cmake_file_name", "libmongoc-1.0")
		self.cpp_info.components["mongoc"].set_property("cmake_target_name", f"mongo::{mongoc_target}")
		self.cpp_info.components["mongoc"].set_property("pkg_config_name", "libmongoc-1.0" if self.options.shared else "libmongoc-static-1.0")

		self.cpp_info.components["mongoc"].builddirs.append(self._module_subfolder)

		self.cpp_info.components["mongoc"].includedirs = [os.path.join("include", "libmongoc-1.0")]
		self.cpp_info.components["mongoc"].libs = ["mongoc-1.0" if self.options.shared else "mongoc-static-1.0"]


		# bson
		bson_target = "bson_shared" if self.options.shared else "bson_static"
		self.cpp_info.components["bson"].set_property("cmake_file_name", "libbson-1.0")
		self.cpp_info.components["bson"].set_property("cmake_target_name", f"mongo::{bson_target}")
		self.cpp_info.components["bson"].set_property("pkg_config_name", "libbson-1.0" if self.options.shared else "libbson-static-1.0")

		self.cpp_info.components["bson"].builddirs.append(self._module_subfolder)

		self.cpp_info.components["bson"].includedirs = [os.path.join("include", "libbson-1.0")]
		self.cpp_info.components["bson"].libs = ["bson-1.0" if self.options.shared else "bson-static-1.0"]
		if not self.options.shared:
			self.cpp_info.components["bson"].defines = ["BSON_STATIC"]
		if self.settings.os in ["Linux", "FreeBSD"]:
			self.cpp_info.components["bson"].system_libs = ["m", "pthread", "rt"]
		elif self.settings.os == "Windows":
			self.cpp_info.components["bson"].system_libs = ["ws2_32"]

