# Generate library with only C++ source files.
# This library will be used by the binding library and dependent libraries.
add_library(
    models_cpp
    SHARED
    Coords.cpp
    CoordsList.cpp
    Polar.cpp
    Pose.cpp
    PoseBuffer.cpp
)
target_include_directories(
    models_cpp
    PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${PROJECT_SOURCE_DIR}/cogip/cpp/libraries/utils/include
)
set_target_properties(models_cpp PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/..)

# Generate library with binding.
nanobind_add_module(
    models
    NB_SHARED STABLE_ABI LTO
    binding.cpp
)
target_link_libraries(models PUBLIC models_cpp)
set_target_properties(models PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/..)

# Install the library.
install(
    TARGETS models_cpp models
    LIBRARY DESTINATION cogip/cpp/libraries
)

# Generate stub files that are needed to enable static type checking and autocompletion in Python IDEs.
nanobind_add_stub(
    models_stub
    MODULE cogip.cpp.libraries.models
    OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/__init__.pyi
    MARKER_FILE ${CMAKE_CURRENT_BINARY_DIR}/py.typed
    PYTHON_PATH ${CMAKE_BINARY_DIR}
    DEPENDS models
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
    DESTINATION cogip/cpp/libraries
)
install(
    FILES ${CMAKE_CURRENT_BINARY_DIR}/__init__.pyi
    RENAME models.pyi
    DESTINATION cogip/cpp/libraries
)
