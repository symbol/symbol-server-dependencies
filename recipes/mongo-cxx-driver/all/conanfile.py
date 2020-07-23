from conans import ConanFile, CMake, tools
import os

class MongoCxxConan(ConanFile):
    name = "mongo-cxx-driver"
    version = "3.4.0-nem"
    description = "C++ Driver for MongoDB"
    topics = ("conan", "mongocxx", "libmongocxx", "mongodb", "cpp")
    url = "https://github.com/nemtech/symbol-server-dependencies.git",
    homepage = "https://github.com/nemtech/mongo-cxx-driver"
    license = "Apache-2.0"
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"

    settings =  "os", "compiler", "arch", "build_type"
    options = {"shared": [True, False]}
    default_options = {"shared": True}

    _source_subfolder = "source_subfolder"

    requires = 'mongo-c-driver/[~=1.15]@nemtech/stable'

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])

        extracted_dir = self.name + "-r" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def configure(self):
        pass

    def _configure_cmake(self):
        cmake = CMake(self)

        cmake.definitions["CMAKE_CXX_STANDARD"] = "17"

        if self.settings.compiler == "Visual Studio":
            cmake.definitions["CMAKE_CXX_FLAGS"] = "/Zc:__cplusplus"

        cmake.configure()
        return cmake

    def build(self):
        mongocxx_cmake_file = os.path.join(self._source_subfolder, 'src', 'mongocxx', 'CMakeLists.txt')
        bsoncxx_cmake_file = os.path.join(self._source_subfolder, 'src', 'bsoncxx', 'CMakeLists.txt')
        tools.replace_in_file(mongocxx_cmake_file, 'add_subdirectory(test)', '')
        tools.replace_in_file(bsoncxx_cmake_file, 'add_subdirectory(test)', '')

        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern="LICENSE*", src=self._source_subfolder)
        self.copy(pattern="*.hpp", dst="include/bsoncxx", src=self._source_subfolder + "/src/bsoncxx", keep_path=True)
        self.copy(pattern="*.hpp", dst="include/mongocxx", src=self._source_subfolder + "/src/mongocxx", keep_path=True)
        self.copy(pattern="*.dll", dst="bin", src="bin", keep_path=False)
        self.copy(pattern="lib*cxx.lib", dst="lib", src="lib", keep_path=False)
        self.copy(pattern="lib*cxx.a", dst="lib", src="lib", keep_path=False)
        self.copy(pattern="lib*cxx.so*", dst="lib", src="lib", keep_path=False)
        self.copy(pattern="lib*cxx.dylib", dst="lib", src="lib", keep_path=False)
        self.copy(pattern="lib*cxx._noabi.dylib", dst="lib", src="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = ['mongocxx', 'bsoncxx']

