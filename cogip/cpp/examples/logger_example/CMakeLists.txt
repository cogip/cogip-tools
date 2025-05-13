# Generate library with source code and binding.
nanobind_add_module(
    logger_example
    NB_SHARED STABLE_ABI LTO
    binding.cpp
    logger_example.cpp
)
target_include_directories(
    logger_example
    PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${PROJECT_SOURCE_DIR}/cogip/cpp/libraries/logger/include
)
target_link_libraries(
    logger_example
    PUBLIC
    logger_cpp
)

set_target_properties(logger_example PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/..)

# Install the library.
install(
    TARGETS logger_example
    LIBRARY DESTINATION cogip/cpp/examples
)

# Generate stub files that are needed to enable static type checking and autocompletion in Python IDEs.
nanobind_add_stub(
    logger_example_stub
    MODULE cogip.cpp.examples.logger_example
    OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/__init__.pyi
    MARKER_FILE ${CMAKE_CURRENT_BINARY_DIR}/py.typed
    PYTHON_PATH ${CMAKE_BINARY_DIR}
    DEPENDS logger_example
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
    DESTINATION cogip/cpp/examples
)
install(
    FILES ${CMAKE_CURRENT_BINARY_DIR}/__init__.pyi
    RENAME logger_example.pyi
    DESTINATION cogip/cpp/examples
)
