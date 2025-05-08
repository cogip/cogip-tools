# Generate library with only C++ source files.
# This library will be used by the binding library and dependent libraries.
add_library(
    logger_cpp
    SHARED
    PythonLogger.cpp
)
set_target_properties(logger_cpp PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/..)
target_include_directories(
    logger_cpp
    PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
# Generate library with source code and binding.
nanobind_add_module(
    logger
    NB_SHARED STABLE_ABI LTO
    binding.cpp
)
target_link_libraries(logger PUBLIC logger_cpp)
set_target_properties(logger PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/..)

# Install the library.
install(
    TARGETS logger_cpp logger
    LIBRARY DESTINATION cogip/cpp/libraries
)

# Generate stub files that are needed to enable static type checking and autocompletion in Python IDEs.
nanobind_add_stub(
    logger_stub
    MODULE cogip.cpp.libraries.logger
    OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/__init__.pyi
    MARKER_FILE ${CMAKE_CURRENT_BINARY_DIR}/py.typed
    PYTHON_PATH ${CMAKE_BINARY_DIR}
    DEPENDS logger
    VERBOSE
    INSTALL_TIME
)

# Copy stub files into the source directory.
# so it will be available if the package is installed in editable mode (default mode).
install(
    FILES ${CMAKE_CURRENT_BINARY_DIR}/__init__.pyi ${CMAKE_CURRENT_BINARY_DIR}/py.typed
    DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}
)

# Copy stub files into the install directory so it will be added to the wheel package.
install(
    FILES ${CMAKE_CURRENT_BINARY_DIR}/py.typed
    DESTINATION cogip/cpp/libraries
)
install(
    FILES ${CMAKE_CURRENT_BINARY_DIR}/__init__.pyi
    RENAME logger.pyi
    DESTINATION cogip/cpp/libraries
)
