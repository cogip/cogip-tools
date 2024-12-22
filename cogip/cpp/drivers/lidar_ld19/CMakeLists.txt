include_directories(
    include
)

# Find and link libserial
find_package(PkgConfig REQUIRED)
pkg_check_modules(LibSerial REQUIRED libserial)
add_definitions(${LibSerial_CFLAGS_OTHER})
include_directories(${LibSerial_INCLUDE_DIRS})
link_directories(${LibSerial_LIBRARY_DIRS})

nanobind_add_module(
    lidar_ld19
    binding.cpp
    ldlidar_driver.cpp
    ldlidar_protocol.cpp
)

target_link_libraries(lidar_ld19 PRIVATE ${LibSerial_LIBRARIES})

# Generate stub files that are needed to enable static type checking and autocompletion in Python IDEs.
nanobind_add_stub(
    lidar_ld19_stub
    MODULE lidar_ld19
    OUTPUT lidar_ld19.pyi
    MARKER_FILE py.typed
    PYTHON_PATH $<TARGET_FILE_DIR:lidar_ld19>
    DEPENDS lidar_ld19
)

# Install the library.
install(
    TARGETS lidar_ld19
    LIBRARY DESTINATION cogip/cpp/drivers
)

# Copy stub files into the source directory.
# so it will be available if the package is installed in editable mode (default mode).
install(
    FILES ${CMAKE_CURRENT_BINARY_DIR}/py.typed
    DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}
)
install(
    FILES ${CMAKE_CURRENT_BINARY_DIR}/lidar_ld19.pyi
    DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}
    RENAME __init__.pyi
)

# Copy stub files into the install directory so it will be added to the wheel package.
install(
    FILES ${CMAKE_CURRENT_BINARY_DIR}/py.typed ${CMAKE_CURRENT_BINARY_DIR}/lidar_ld19.pyi
    DESTINATION cogip/cpp/drivers
)
