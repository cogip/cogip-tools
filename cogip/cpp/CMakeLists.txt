list(
    APPEND
    CMAKE_INSTALL_RPATH
    "$ORIGIN/../libraries"
    "$ORIGIN/../drivers"
)

add_subdirectory(examples)
add_subdirectory(drivers)
add_subdirectory(libraries)
