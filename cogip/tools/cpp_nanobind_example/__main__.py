#!/usr/bin/env python3
from numpy.typing import NDArray

from cogip.cpp.nanobind_example import NanobindExample


def main():
    """
    Example calling a function from a C++ class built in C++ extension with a Nanobind binding.

    During installation of cogip-tools, a script called `cogip-cpp-nanobind-example`
    will be created using this function as entrypoint.
    """
    example = NanobindExample()
    print(example.get_message())
    data: NDArray = example.get_data()
    print(f"data type: {data.__class__}")
    print(f"data shape: {data.shape}")
    print(f"data = \n{data}")


if __name__ == "__main__":
    main()
