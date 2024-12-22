# Include directories
include_directories(
    include
)

# Create shared library
add_library(
    cpp_cython_example
    STATIC
    cython_example.cpp
)
target_compile_options(
    cpp_cython_example
    PRIVATE
    -fPIC
)

# Add the Cython transpile step
cython_transpile(
    cython_example.pyx
    LANGUAGE CXX
    CYTHON_ARGS --cplus -3
    OUTPUT_VARIABLE CYTHON_EXAMPLE_CPP
)

# Define the Python extension using Cython
python_add_library(cython_example MODULE "${CYTHON_EXAMPLE_CPP}" WITH_SOABI)

target_link_libraries(cython_example PRIVATE cpp_cython_example Python::Module)

install(
    TARGETS cython_example
    LIBRARY DESTINATION cogip/cpp/
)
