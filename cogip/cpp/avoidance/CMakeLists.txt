# Include directories
include_directories(
    ${CMAKE_SOURCE_DIR}/avoidance/lib/avoidance/include
    ${CMAKE_SOURCE_DIR}/avoidance/lib/cogip_defs/include
    ${CMAKE_SOURCE_DIR}/avoidance/lib/logger/include
    ${CMAKE_SOURCE_DIR}/avoidance/lib/obstacles/include
    ${CMAKE_SOURCE_DIR}/avoidance/lib/path/include
    ${CMAKE_SOURCE_DIR}/avoidance/lib/trigonometry/include
    ${CMAKE_SOURCE_DIR}/avoidance/lib/utils/include
)

# Source files
set(SOURCES
    ${CMAKE_SOURCE_DIR}/avoidance/lib/avoidance/Avoidance.cpp
    ${CMAKE_SOURCE_DIR}/avoidance/lib/cogip_defs/Coords.cpp
    ${CMAKE_SOURCE_DIR}/avoidance/lib/obstacles/ObstacleCircle.cpp
    ${CMAKE_SOURCE_DIR}/avoidance/lib/obstacles/ObstaclePolygon.cpp
    ${CMAKE_SOURCE_DIR}/avoidance/lib/obstacles/ObstacleRectangle.cpp
    ${CMAKE_SOURCE_DIR}/avoidance/lib/path/Pose.cpp
    ${CMAKE_SOURCE_DIR}/avoidance/lib/utils/utils.cpp
)

# Create shared library avoidance.so
add_library(libavoidance STATIC ${SOURCES})
target_compile_options(libavoidance PRIVATE -fPIC)

# Define the .pyx file to be compiled
set(PYTHON_MODULE_SRC ${CMAKE_SOURCE_DIR}/avoidance/avoidance.pyx)

# Add the cython transpile step
cython_transpile(${PYTHON_MODULE_SRC}
                LANGUAGE CXX
                CYTHON_ARGS
                    --cplus -3
                OUTPUT_VARIABLE LIBAVOIDANCE)

# Define the Python extension using Cython
python_add_library(avoidance MODULE "${LIBAVOIDANCE}" WITH_SOABI)

target_link_libraries(avoidance PRIVATE libavoidance Python::Module)

install(TARGETS avoidance
    LIBRARY DESTINATION cogip/cpp/
)
