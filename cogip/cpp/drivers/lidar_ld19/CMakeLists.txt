# Find and link libserial
find_package(PkgConfig REQUIRED)
pkg_check_modules(LibSerial REQUIRED libserial)
add_definitions(${LibSerial_CFLAGS_OTHER})
include_directories(${LibSerial_INCLUDE_DIRS})
link_directories(${LibSerial_LIBRARY_DIRS})

nanobind_add_module(
    lidar_ld19
    NB_SHARED STABLE_ABI LTO
    binding.cpp
    ldlidar_driver.cpp
    ldlidar_protocol.cpp
)
target_include_directories(
    lidar_ld19
    PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
target_link_libraries(lidar_ld19 PRIVATE ${LibSerial_LIBRARIES} models shared_memory)
set_target_properties(lidar_ld19 PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/..)

# Install the library.
install(
    TARGETS lidar_ld19
    LIBRARY DESTINATION cogip/cpp/drivers
)

# Generate stub files that are needed to enable static type checking and autocompletion in Python IDEs.
nanobind_add_stub(
    lidar_ld19_stub
    MODULE cogip.cpp.drivers.lidar_ld19
    OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/__init__.pyi
    MARKER_FILE ${CMAKE_CURRENT_BINARY_DIR}/py.typed
    PYTHON_PATH ${CMAKE_BINARY_DIR}
    DEPENDS lidar_ld19
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
    DESTINATION cogip/cpp/drivers
)
install(
    FILES ${CMAKE_CURRENT_BINARY_DIR}/__init__.pyi
    RENAME lidar_ld19.pyi
    DESTINATION cogip/cpp/drivers
)
