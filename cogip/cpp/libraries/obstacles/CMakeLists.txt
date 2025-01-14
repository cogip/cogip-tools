# Generate library with only C++ source files.
# This library will be used by the binding library and dependent libraries.
add_library(
    obstacles_cpp
    SHARED
    ObstacleCircle.cpp
    ObstaclePolygon.cpp
    ObstacleRectangle.cpp
)
set_target_properties(obstacles_cpp PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/..)
target_include_directories(
    obstacles_cpp
    PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${PROJECT_SOURCE_DIR}/cogip/cpp/libraries/utils/include
    ${PROJECT_SOURCE_DIR}/cogip/cpp/libraries/models/include
)
target_link_libraries(
    obstacles_cpp
    PUBLIC
    models_cpp
)

# Generate library with source code and binding.
nanobind_add_module(
    obstacles
    NB_SHARED STABLE_ABI LTO
    binding.cpp
)
target_link_libraries(obstacles PUBLIC obstacles_cpp)
set_target_properties(obstacles PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/..)

# Install the library.
install(
    TARGETS obstacles_cpp obstacles
    LIBRARY DESTINATION cogip/cpp/libraries
)

# Generate stub files that are needed to enable static type checking and autocompletion in Python IDEs.
nanobind_add_stub(
    obstacles_stub
    MODULE cogip.cpp.libraries.obstacles
    OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/__init__.pyi
    MARKER_FILE ${CMAKE_CURRENT_BINARY_DIR}/py.typed
    PYTHON_PATH ${CMAKE_BINARY_DIR}
    DEPENDS obstacles models_stub
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
    RENAME obstacles.pyi
    DESTINATION cogip/cpp/libraries
)
