# example.pyx

# cython: profile=True

from libcpp.string cimport string

cdef extern from "cython_example/cython_example.hpp" namespace "":
    cdef cppclass CythonExample:
        CythonExample()
        string getMessage() const

# Wrapping PyCythonExample class for Python
cdef class PyCythonExample:
    cdef CythonExample* cpp_instance

    def __cinit__(self):
        self.cpp_instance = new CythonExample()

    def __dealloc__(self):
        del self.cpp_instance

    def get_message(self) -> str:
        cdef string message = self.cpp_instance.getMessage()
        return message.decode("utf-8")
