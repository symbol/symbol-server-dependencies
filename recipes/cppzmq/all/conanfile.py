## patch, patches ZeroMq cmake, so that it:
##  * checks properly that there's a conan cmake zeromq target
##  * links with libzmq (shared) so that doing find_package(cppzmq) should define libzmq target
##

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain
from conan.tools.files import apply_conandata_patches, copy, get
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version


class CppZmqConan(ConanFile):
	name = "cppzmq"

	description = "C++ binding for ZeroMQ"
	topics = ("conan", "cppzmq", "zmq-cpp", "zmq", "cpp-bind")
	url = "https://github.com/symbol/symbol-server-dependencies",
	homepage = "https://github.com/zeromq/cppzmq"
	license = "MIT"
	exports_sources = "patches/*.patch"
	package_type = "header-library"

	settings = "os", "compiler", "build_type", "arch"

	def requirements(self):
		self.requires("zeromq/4.3.5@nemtech/stable", transitive_libs=True, run=True)

	def source(self):
		get(self, **self.conan_data["sources"][self.version], strip_root=True)

	def config_options(self):
		if self.settings.os == "Windows":
			if is_msvc(self) and Version(self.settings.compiler.version.value) < 15:
				raise ConanInvalidConfiguration("{} {}, 'Symbol' packages do not support Visual Studio < 15".format(self.name, self.version))

	def generate(self):
		tc = CMakeToolchain(self)
		tc.cache_variables["CPPZMQ_BUILD_TESTS"] = False
		if "Macos" == self.settings.os:
			tc.blocks["rpath"].skip_rpath = False

		tc.generate()
		deps = CMakeDeps(self)
		deps.generate()

	def build(self):
		apply_conandata_patches(self)
		cmake = CMake(self)
		cmake.configure()
		cmake.build()

	def package(self):
		copy(self, pattern="LICENSE", dst="licenses", src=self.source_folder)
		cmake = CMake(self)
		cmake.install()

	def compatibility(self):
		self.info.clear()


	def package_info(self):
		self.cpp_info.set_property("cmake_file_name", "cppzmq")
		self.cpp_info.set_property("cmake_target_name", "cppzmq")
		self.cpp_info.bindirs = []
		self.cpp_info.libdirs = []
