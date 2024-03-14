from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import cross_building
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import collect_libs, copy, get, rmdir
from conan.tools.microsoft import is_msvc
from conan.tools.scm import Version
import os


class BenchmarkConan(ConanFile):
	name = "benchmark"
	description = "A microbenchmark support library."
	topics = ("conan", "benchmark", "google", "microbenchmark")
	url = "https://github.com/symbol/symbol-server-dependencies"
	homepage = "https://github.com/google/benchmark"
	license = "Apache-2.0"
	package_type = "library"

	settings = "arch", "build_type", "compiler", "os"
	options = {
		"shared": [True, False],
		"fPIC": [True, False],
		"enable_lto": [True, False],
		"enable_exceptions": [True, False]
	}
	default_options = {"shared": False, "fPIC": True, "enable_lto": False, "enable_exceptions": True}

	def source(self):
		get(self, **self.conan_data["sources"][self.version], strip_root=True)

	def config_options(self):
		if self.settings.os == "Windows":
			if is_msvc(self) and Version(self.settings.compiler.version.value) < 15:
				raise ConanInvalidConfiguration("{} {}, 'Symbol' packages do not support Visual Studio < 15".format(self.name, self.version))

			del self.options.fPIC

	def configure(self):
		if self.settings.os == "Windows" and self.options.shared:
			raise ConanInvalidConfiguration("Windows shared builds are not supported right now, see issue #639")

	def is_arch_64_bit(self):
		return "64" in str(self.settings.arch) or self.settings.arch in ["armv8", "armv8.3", "armv9"]

	def layout(self):
		cmake_layout(self, src_folder='src')

	def generate(self):
		tc = CMakeToolchain(self)

		tc.cache_variables["BENCHMARK_ENABLE_TESTING"] = "OFF"
		tc.cache_variables["BENCHMARK_ENABLE_GTEST_TESTS"] = "OFF"
		tc.cache_variables["BENCHMARK_ENABLE_LTO"] = "ON" if self.options.enable_lto else "OFF"
		tc.cache_variables["BENCHMARK_ENABLE_EXCEPTIONS"] = "ON" if self.options.enable_exceptions else "OFF"

		# See https://github.com/google/benchmark/pull/638 for Windows 32 build explanation
		if self.settings.os != "Windows":
			if cross_building(self):
				tc.cache_variables["HAVE_STD_REGEX"] = False
				tc.cache_variables["HAVE_POSIX_REGEX"] = False
				tc.cache_variables["HAVE_STEADY_CLOCK"] = False
			else:
				tc.cache_variables["BENCHMARK_BUILD_32_BITS"] = "OFF" if self.is_arch_64_bit() else "ON"
			tc.cache_variables["BENCHMARK_USE_LIBCXX"] = "ON" if (str(self.settings.compiler.libcxx) == "libc++") else "OFF"
		else:
			tc.cache_variables["BENCHMARK_USE_LIBCXX"] = "OFF"

		if "Macos" == self.settings.os:
			tc.blocks["rpath"].skip_rpath = False

		tc.generate()

	def build(self):
		cmake = CMake(self)
		cmake.configure()
		cmake.build()

	def package(self):
		copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
		cmake = CMake(self)
		cmake.install()

		rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

	def package_info(self):
		self.cpp_info.set_property("cmake_file_name", "benchmark")
		self.cpp_info.set_property("pkg_config_name", "benchmark")

		self.cpp_info.components["_benchmark"].set_property("cmake_target_name", "benchmark::benchmark")
		self.cpp_info.components["_benchmark"].libs = ["benchmark"]
		if Version(self.version) >= Version("1.7.0") and not self.options.shared:
			self.cpp_info.components["_benchmark"].defines.append("BENCHMARK_STATIC_DEFINE")

		self.cpp_info.libs = collect_libs(self)
		if self.settings.os == "Linux":
			self.cpp_info.components["_benchmark"].system_libs.extend(["pthread", "rt", "m"])
		elif self.settings.os == "Windows":
			self.cpp_info.components["_benchmark"].system_libs.append("shlwapi")
