# Generate library with source code and binding.
nanobind_add_module(
    avoidance
    NB_SHARED STABLE_ABI LTO
    binding.cpp
    Avoidance.cpp
)
target_include_directories(
    avoidance
    PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${PROJECT_SOURCE_DIR}/cogip/cpp/libraries/logger/include
    ${PROJECT_SOURCE_DIR}/cogip/cpp/libraries/models/include
    ${PROJECT_SOURCE_DIR}/cogip/cpp/libraries/obstacles/include
    ${PROJECT_SOURCE_DIR}/cogip/cpp/libraries/utils/include
)
target_link_libraries(
    avoidance
    PUBLIC
    logger_cpp
    models_cpp
    obstacles_cpp
)
set_target_properties(avoidance PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/..)

# Install the library.
install(
    TARGETS avoidance
    LIBRARY DESTINATION cogip/cpp/libraries
)

# Generate stub files that are needed to enable static type checking and autocompletion in Python IDEs.
nanobind_add_stub(
    avoidance_stub
    MODULE cogip.cpp.libraries.avoidance
    OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/__init__.pyi
    MARKER_FILE ${CMAKE_CURRENT_BINARY_DIR}/py.typed
    PYTHON_PATH ${CMAKE_BINARY_DIR}
    DEPENDS avoidance models_stub obstacles_stub
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
    RENAME avoidance.pyi
    DESTINATION cogip/cpp/libraries
)
