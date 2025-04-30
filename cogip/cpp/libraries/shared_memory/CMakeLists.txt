# Generate library with only C++ source files.
# This library will be used by the binding library and dependent libraries.
add_library(
    shared_memory_cpp
    SHARED
    WritePriorityLock.cpp
    SharedMemory.cpp
)
set_target_properties(shared_memory_cpp PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/..)
target_include_directories(
    shared_memory_cpp
    PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${PROJECT_SOURCE_DIR}/cogip/cpp/libraries/utils/include
    ${PROJECT_SOURCE_DIR}/cogip/cpp/libraries/models/include
    ${PROJECT_SOURCE_DIR}/cogip/cpp/libraries/obstacles/include
)
target_link_libraries(
    shared_memory_cpp
    PUBLIC
    models_cpp
    obstacles_cpp
)

# Generate library with source code and binding.
nanobind_add_module(
    shared_memory
    NB_SHARED STABLE_ABI LTO
    binding.cpp
)
target_link_libraries(shared_memory PUBLIC shared_memory_cpp)
set_target_properties(shared_memory PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/..)

# Install the library.
install(
    TARGETS shared_memory_cpp shared_memory
    LIBRARY DESTINATION cogip/cpp/libraries
)

# Generate stub files that are needed to enable static type checking and autocompletion in Python IDEs.
nanobind_add_stub(
    shared_memory_stub
    MODULE cogip.cpp.libraries.shared_memory
    OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/__init__.pyi
    MARKER_FILE ${CMAKE_CURRENT_BINARY_DIR}/py.typed
    PYTHON_PATH ${CMAKE_BINARY_DIR}
    DEPENDS shared_memory models_stub obstacles_stub
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
    RENAME shared_memory.pyi
    DESTINATION cogip/cpp/libraries
)
