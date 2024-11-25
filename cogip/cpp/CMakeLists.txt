cmake_minimum_required(VERSION 3.28)
project(${SKBUILD_PROJECT_NAME})

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)

# Python packages
find_package(Python COMPONENTS Interpreter Development REQUIRED)

# Find Cython .cmake files
file(GLOB_RECURSE FIND_CYTHON_CMAKE_FILE "${PROJECT_SOURCE_DIR}/*Cython.cmake")
get_filename_component(FIND_CYTHON_CMAKE_DIR "${FIND_CYTHON_CMAKE_FILE}" DIRECTORY)
list( APPEND CMAKE_MODULE_PATH ${FIND_CYTHON_CMAKE_DIR} )
# Cython packages
find_package(Cython MODULE REQUIRED VERSION 3.1.0)
include(UseCython)

# Include directories
include_directories(${PYTHON_INCLUDE_DIRS})

#add_subdirectory(example)
add_subdirectory(avoidance)
