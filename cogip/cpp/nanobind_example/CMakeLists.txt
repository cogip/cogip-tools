include_directories(
    include
)

# Generate library with source code and binding.
nanobind_add_module(
    nanobind_example
    binding.cpp
    nanobind_example.cpp
)

# Generate stub files that are needed to enable static type checking and autocompletion in Python IDEs.
nanobind_add_stub(
    nanobind_example_stub
    MODULE nanobind_example
    OUTPUT nanobind_example.pyi
    MARKER_FILE py.typed
    PYTHON_PATH $<TARGET_FILE_DIR:nanobind_example>
    DEPENDS nanobind_example
)

# Install the library.
install(
    TARGETS nanobind_example
    LIBRARY DESTINATION cogip/cpp/
)

# Copy stub files into the source directory.
# so it will be available if the package is installed in editable mode (default mode).
install(
    FILES ${CMAKE_CURRENT_BINARY_DIR}/py.typed
    DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}
)
install(
    FILES ${CMAKE_CURRENT_BINARY_DIR}/nanobind_example.pyi
    DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}
    RENAME __init__.pyi
)

# Copy stub files into the install directory so it will be added to the wheel package.
install(
    FILES ${CMAKE_CURRENT_BINARY_DIR}/py.typed ${CMAKE_CURRENT_BINARY_DIR}/nanobind_example.pyi
    DESTINATION cogip/cpp
)
