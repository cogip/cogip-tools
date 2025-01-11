# Generate library with source code and binding.
nanobind_add_module(
    nanobind_example
    NB_SHARED STABLE_ABI LTO
    binding.cpp
    nanobind_example.cpp
)
target_include_directories(
    nanobind_example
    PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
set_target_properties(nanobind_example PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/..)

# Install the library.
install(
    TARGETS nanobind_example
    LIBRARY DESTINATION cogip/cpp/examples
)

# Generate stub files that are needed to enable static type checking and autocompletion in Python IDEs.
nanobind_add_stub(
    nanobind_example_stub
    MODULE cogip.cpp.examples.nanobind_example
    OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/__init__.pyi
    MARKER_FILE ${CMAKE_CURRENT_BINARY_DIR}/py.typed
    PYTHON_PATH ${CMAKE_BINARY_DIR}
    DEPENDS nanobind_example
    VERBOSE
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
    DESTINATION cogip/cpp/examples
)
install(
    FILES ${CMAKE_CURRENT_BINARY_DIR}/__init__.pyi
    RENAME nanobind_example.pyi
    DESTINATION cogip/cpp/examples
)
