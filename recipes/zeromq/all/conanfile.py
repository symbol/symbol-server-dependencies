from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, collect_libs, copy, export_conandata_patches, get, rmdir
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version
import os


class ZeroMQConan(ConanFile):
	name = "zeromq"
	description = "ZeroMQ is a community of projects focused on decentralized messaging and computing"
	topics = ("conan", "zmq", "libzmq", "message-queue", "asynchronous")
	url = "https://github.com/symbol/symbol-server-dependencies",
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

	def export_sources(self):
		export_conandata_patches(self)

	def source(self):
		get(self, **self.conan_data["sources"][self.version], strip_root=True)

	def config_options(self):
		if self.settings.os == "Windows":
			if is_msvc(self) and Version(self.settings.compiler.version.value) < 15:
				raise ConanInvalidConfiguration(
					"{} {}, 'Symbol' packages do not support Visual Studio < 15".format(self.name, self.version))

			del self.options.fPIC

	def configure(self):
		if self.options.shared:
			self.options.rm_safe("fPIC")

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
		apply_conandata_patches(self)
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

		self.cpp_info.components["libzmq"].set_property("cmake_target_name", "libzmq")
		self.cpp_info.components["libzmq"].libs = collect_libs(self)
		if self.settings.os == "Windows":
			self.cpp_info.components["libzmq"].system_libs = ["iphlpapi", "ws2_32"]
		elif self.settings.os == "Linux":
			self.cpp_info.components["libzmq"].system_libs = ["pthread", "rt", "m"]
		if not self.options.shared:
			self.cpp_info.components["libzmq"].defines.append("ZMQ_STATIC")
