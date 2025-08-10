# Find and link libserial
find_package(PkgConfig REQUIRED)
pkg_check_modules(LibSerial REQUIRED libserial)
add_definitions(${LibSerial_CFLAGS_OTHER})
include_directories(${LibSerial_INCLUDE_DIRS})
link_directories(${LibSerial_LIBRARY_DIRS})

nanobind_add_module(
    ydlidar_g2
    NB_SHARED STABLE_ABI LTO
    binding.cpp
    timer.cpp
    YDLidar.cpp
    YDLidarDriver.cpp
)

target_include_directories(
    ydlidar_g2
    PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
target_link_libraries(ydlidar_g2 PRIVATE ${LibSerial_LIBRARIES} shared_memory)
set_target_properties(ydlidar_g2 PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/..)

# Install the library.
install(
    TARGETS ydlidar_g2
    LIBRARY DESTINATION cogip/cpp/drivers
)

# Generate stub files that are needed to enable static type checking and autocompletion in Python IDEs.
nanobind_add_stub(
    ydlidar_g2_stub
    MODULE cogip.cpp.drivers.ydlidar_g2
    OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/__init__.pyi
    MARKER_FILE ${CMAKE_CURRENT_BINARY_DIR}/py.typed
    PYTHON_PATH ${CMAKE_BINARY_DIR}
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
    RENAME ydlidar_g2.pyi
    DESTINATION cogip/cpp/drivers
)
