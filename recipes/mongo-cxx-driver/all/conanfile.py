from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import get
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version
import os

class MongoCxxConan(ConanFile):
	name = "mongo-cxx-driver"
	description = "C++ Driver for MongoDB"
	topics = ("conan", "mongocxx", "libmongocxx", "mongodb", "cpp")
	url = "https://github.com/symbol/symbol-server-dependencies",
	homepage = "https://github.com/mongodb/mongo-cxx-driver"
	license = "Apache-2.0"
	package_type = "library"

	settings = "os", "compiler", "arch", "build_type"
	options = {"shared": [True, False]}
	default_options = {"shared": True}

	def requirements(self):
		self.requires("mongo-c-driver/1.30.0@nemtech/stable", transitive_libs=True, run=True)

	def layout(self):
		cmake_layout(self, src_folder="src")

	def source(self):
		get(self, **self.conan_data["sources"][self.version], strip_root=True)

	def config_options(self):
		if self.settings.os == "Windows":
			if is_msvc(self) and Version(self.settings.compiler.version.value) < 15:
				raise ConanInvalidConfiguration("{} {}, 'Symbol' packages do not support Visual Studio < 15".format(self.name, self.version))

			self.options.rm_safe("fPIC")

	def configure(self):
		pass

	def generate(self):
		tc = CMakeToolchain(self)

		tc.cache_variables["CMAKE_CXX_STANDARD"] = "17"
		tc.cache_variables["BUILD_VERSION"] = self.version
		tc.cache_variables["ENABLE_TESTS"] = False
		if is_msvc(self):
			tc.cache_variables["CMAKE_CXX_FLAGS"] = "/Zc:__cplusplus /EHsc"

		if Version(self.version) >= "3.10.0" and is_msvc(self):
			tc.variables["ENABLE_ABI_TAG_IN_LIBRARY_FILENAMES"] = False

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
		cmake = CMake(self)
		cmake.install()

	def package_info(self):
		mongocxx_target = "mongocxx_shared" if self.options.shared else "mongocxx_static"
		self.cpp_info.set_property("cmake_file_name", "mongocxx")
		self.cpp_info.set_property("cmake_target_name", f"mongo::{mongocxx_target}")

		# mongocxx
		self.cpp_info.components["mongocxx"].set_property("cmake_target_name", f"mongo::{mongocxx_target}")
		self.cpp_info.components["mongocxx"].set_property("pkg_config_name", "libmongocxx" if self.options.shared else "libmongocxx-static")

		self.cpp_info.components["mongocxx"].libs = ["mongocxx" if self.options.shared else "mongocxx-static"]
		if not self.options.shared:
			self.cpp_info.components["mongocxx"].defines.append("MONGOCXX_STATIC")
		self.cpp_info.components["mongocxx"].requires = ["mongo-c-driver::mongoc", "bsoncxx"]

		# The header files are in v_noabi -  https://mongocxx.org/mongocxx-v3/tutorial/
		self.cpp_info.components["mongocxx"].includedirs.extend([os.path.join("include", "mongocxx", "v_noabi")])

		# bsoncxx
		bsoncxx_target = "bsoncxx_shared" if self.options.shared else "bsoncxx_static"
		self.cpp_info.components["bsoncxx"].set_property("cmake_target_name", f"mongo::{bsoncxx_target}")
		self.cpp_info.components["bsoncxx"].set_property("pkg_config_name", "libbsoncxx" if self.options.shared else "libbsoncxx-static")

		# The header files are in v_noabi -  https://mongocxx.org/mongocxx-v3/tutorial/
		self.cpp_info.components["bsoncxx"].libs = ["bsoncxx" if self.options.shared else "bsoncxx-static"]

		self.cpp_info.components["bsoncxx"].includedirs.extend([os.path.join("include", "bsoncxx", "v_noabi")])
		if not self.options.shared:
			self.cpp_info.components["bsoncxx"].defines = ["BSONCXX_STATIC"]
		self.cpp_info.components["bsoncxx"].requires = ["mongo-c-driver::bson"]
