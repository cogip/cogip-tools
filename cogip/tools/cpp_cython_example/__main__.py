#!/usr/bin/env python3
from cogip.cpp.cython_example import PyCythonExample


def main():
    """
    Example calling a function from a C++ class built in C++ extension with a Cython binding.

    During installation of cogip-tools, a script called `cogip-cpp-cython-example`
    will be created using this function as entrypoint.
    """
    example = PyCythonExample()
    print(example.get_message())


if __name__ == "__main__":
    main()
