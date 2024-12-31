cmake_minimum_required(VERSION 3.28)
project(${SKBUILD_PROJECT_NAME})

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)

if (NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build." FORCE)
  set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS "Debug" "Release" "MinSizeRel" "RelWithDebInfo")
endif()

# Python packages
find_package(Python COMPONENTS Interpreter Development REQUIRED)
find_package(
  Python 3.12
  REQUIRED COMPONENTS Interpreter Development.Module
)

# Configure support for C++ extensions using Cython binding
file(GLOB_RECURSE FIND_CYTHON_CMAKE_FILE "${PROJECT_SOURCE_DIR}/*Cython.cmake")
get_filename_component(FIND_CYTHON_CMAKE_DIR "${FIND_CYTHON_CMAKE_FILE}" DIRECTORY)
list(APPEND CMAKE_MODULE_PATH ${FIND_CYTHON_CMAKE_DIR})
find_package(Cython MODULE REQUIRED VERSION 3.1.0)
include(UseCython)
include_directories(${PYTHON_INCLUDE_DIRS})

# Configure support for C++ extensions using Nanobind binding
execute_process(
  COMMAND "${Python_EXECUTABLE}" -m nanobind --cmake_dir
  OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE nanobind_DIR)
find_package(nanobind CONFIG REQUIRED)
# Build nanobind shared library separately to install it in the root directory.
nanobind_build_library(nanobind SHARED)
install(
    TARGETS nanobind
    LIBRARY DESTINATION cogip/cpp
)
# Set RPATH globally for all targets
set(CMAKE_INSTALL_RPATH "$ORIGIN" "$ORIGIN/.." "$ORIGIN/../..")
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

add_subdirectory(cogip)
