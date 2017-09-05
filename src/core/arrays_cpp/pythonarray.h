// vi: set expandtab ts=4 sw=4:

/*
 * === UCSF ChimeraX Copyright ===
 * Copyright 2016 Regents of the University of California.
 * All rights reserved.  This software provided pursuant to a
 * license agreement containing restrictions on its disclosure,
 * duplication and use.  For details see:
 * http://www.rbvi.ucsf.edu/chimerax/docs/licensing.html
 * This notice must be embedded in or attached to all copies,
 * including partial copies, of the software or any revisions
 * or derivations thereof.
 * === UCSF ChimeraX Copyright ===
 */

// ----------------------------------------------------------------------------
// Convert multi-dimensional arrays between Python and C++.
//
#ifndef PYTHONARRAY_HEADER_INCLUDED
#define PYTHONARRAY_HEADER_INCLUDED

#include <Python.h>
#include <vector>       // use std::vector<>

#include "imex.h"

#include "rcarray.h"        // use Numeric_Array

using Reference_Counted_Array::Numeric_Array;
using Reference_Counted_Array::Untyped_Array;

//
// Return false if python object is not an array of specified dimension.
//
ARRAYS_IMEX bool array_from_python(PyObject *array, int dim, Numeric_Array *na,
               bool allow_data_copy = true);

//
// Return false if python object is not an array of specified
// dimension or does not have the specified value type.
//
ARRAYS_IMEX bool array_from_python(PyObject *array, int dim,
               Numeric_Array::Value_Type required_type,
               Numeric_Array *na,
               bool allow_data_copy = true);

//
// Recover numpy Python array used to create a C++ array.
// Returns NULL if there is no Python array.
//
ARRAYS_IMEX PyObject *array_python_source(const Untyped_Array &a);

//
// Routines for parsing array arguments with PyArg_ParseTuple().
//
extern "C" {
ARRAYS_IMEX int parse_bool(PyObject *arg, void *b);
ARRAYS_IMEX int parse_float_n2_array(PyObject *arg, void *farray);
ARRAYS_IMEX int parse_float_n3_array(PyObject *arg, void *farray);
ARRAYS_IMEX int parse_writable_float_n3_array(PyObject *arg, void *farray);
ARRAYS_IMEX int parse_double_n3_array(PyObject *arg, void *darray);
ARRAYS_IMEX int parse_writable_double_n3_array(PyObject *arg, void *darray);
ARRAYS_IMEX int parse_uint8_n_array(PyObject *arg, void *carray);
ARRAYS_IMEX int parse_writable_uint8_n_array(PyObject *arg, void *carray);
ARRAYS_IMEX int parse_uint8_n2_array(PyObject *arg, void *carray);
ARRAYS_IMEX int parse_uint8_n3_array(PyObject *arg, void *carray);
ARRAYS_IMEX int parse_uint8_n4_array(PyObject *arg, void *carray);
ARRAYS_IMEX int parse_float_n4_array(PyObject *arg, void *farray);
ARRAYS_IMEX int parse_writable_float_n4_array(PyObject *arg, void *farray);
ARRAYS_IMEX int parse_writable_float_n9_array(PyObject *arg, void *farray);
ARRAYS_IMEX int parse_float_n_array(PyObject *arg, void *farray);
ARRAYS_IMEX int parse_writable_float_n_array(PyObject *arg, void *farray);
ARRAYS_IMEX int parse_double_n_array(PyObject *arg, void *farray);
ARRAYS_IMEX int parse_writable_double_n_array(PyObject *arg, void *farray);
ARRAYS_IMEX int parse_int_3_array(PyObject *arg, void *i3);
ARRAYS_IMEX int parse_float_3_array(PyObject *arg, void *f3);
ARRAYS_IMEX int parse_double_3_array(PyObject *arg, void *f3);
ARRAYS_IMEX int parse_float_4_array(PyObject *arg, void *f4);
ARRAYS_IMEX int parse_float_3x3_array(PyObject *arg, void *f3x3);
ARRAYS_IMEX int parse_double_3x3_array(PyObject *arg, void *d3x3);
ARRAYS_IMEX int parse_float_3x4_array(PyObject *arg, void *f3x4);
ARRAYS_IMEX int parse_double_3x4_array(PyObject *arg, void *d3x4);
ARRAYS_IMEX int parse_writable_float_3d_array(PyObject *arg, void *farray);
ARRAYS_IMEX int parse_int_n_array(PyObject *arg, void *iarray);
ARRAYS_IMEX int parse_int_n2_array(PyObject *arg, void *iarray);
ARRAYS_IMEX int parse_int_n3_array(PyObject *arg, void *iarray);
ARRAYS_IMEX int parse_writable_int_n_array(PyObject *arg, void *iarray);
ARRAYS_IMEX int parse_writable_int_n3_array(PyObject *arg, void *iarray);
ARRAYS_IMEX int parse_1d_array(PyObject *arg, void *array);
ARRAYS_IMEX int parse_2d_array(PyObject *arg, void *array);
ARRAYS_IMEX int parse_3d_array(PyObject *arg, void *array);
ARRAYS_IMEX int parse_array(PyObject *arg, void *array);
ARRAYS_IMEX int parse_writable_array(PyObject *arg, void *array);
ARRAYS_IMEX int parse_float_array(PyObject *arg, void *array);
ARRAYS_IMEX int parse_writable_3d_array(PyObject *arg, void *array);
ARRAYS_IMEX int parse_writable_4d_array(PyObject *arg, void *array);
ARRAYS_IMEX int parse_string_array(PyObject *arg, void *carray);
}

ARRAYS_IMEX bool check_array_size(FArray &a, int n, int m, bool require_contiguous = false);
ARRAYS_IMEX bool check_array_size(FArray &a, int n, bool require_contiguous = false);

//
// Convert a one dimensional sequences of known length from Python to C.
// python_array_to_c() returns false if python object is not
// array of correct size.
//
ARRAYS_IMEX bool python_array_to_c(PyObject *a, int *values, int size);
ARRAYS_IMEX bool python_array_to_c(PyObject *a, float *values, int size);
ARRAYS_IMEX bool python_array_to_c(PyObject *a, float *values, int size0, int size1);
ARRAYS_IMEX bool python_array_to_c(PyObject *a, double *values, int size);
ARRAYS_IMEX bool python_array_to_c(PyObject *a, double *values, int size0, int size1);

ARRAYS_IMEX bool float_2d_array_values(PyObject *farray, int n2, float **f, int *size);

//
// Convert C arrays to Python Numpy arrays.
//
ARRAYS_IMEX PyObject *c_array_to_python(const int *values, int size);
ARRAYS_IMEX PyObject *c_array_to_python(const std::vector<int> &values);
ARRAYS_IMEX PyObject *c_array_to_python(const std::vector<int> &values, int size0, int size1);
ARRAYS_IMEX PyObject *c_array_to_python(const std::vector<float> &values);
ARRAYS_IMEX PyObject *c_array_to_python(const std::vector<float> &values, int size0, int size1);
ARRAYS_IMEX PyObject *c_array_to_python(const float *values, int size);
ARRAYS_IMEX PyObject *c_array_to_python(const double *values, int size);
ARRAYS_IMEX PyObject *c_array_to_python(const int *values, int size0, int size1);
ARRAYS_IMEX PyObject *c_array_to_python(const float *values, int size0, int size1);
ARRAYS_IMEX PyObject *c_array_to_python(const double *values, int size0, int size1);

//
// Create an uninitialized Numpy array.
//
ARRAYS_IMEX PyObject *python_bool_array(int size, unsigned char **data = NULL);
ARRAYS_IMEX PyObject *python_uint8_array(int size, unsigned char **data = NULL);
ARRAYS_IMEX PyObject *python_uint8_array(int size1, int size2, unsigned char **data = NULL);
ARRAYS_IMEX PyObject *python_int_array(int size, int **data = NULL);
ARRAYS_IMEX PyObject *python_int_array(int size1, int size2, int **data = NULL);
ARRAYS_IMEX PyObject *python_unsigned_int_array(int size1, int size2, int size3, unsigned int **data = NULL);
ARRAYS_IMEX PyObject *python_float_array(int size, float **data = NULL);
ARRAYS_IMEX PyObject *python_float_array(int size1, int size2, float **data = NULL);
ARRAYS_IMEX PyObject *python_float_array(int size1, int size2, int size3, float **data = NULL);
ARRAYS_IMEX PyObject *python_double_array(int size, double **data = NULL);
ARRAYS_IMEX PyObject *python_voidp_array(int size, void ***data = NULL);
ARRAYS_IMEX PyObject *python_object_array(int size, PyObject **data = NULL);

ARRAYS_IMEX PyObject *python_none();
ARRAYS_IMEX PyObject *python_bool(bool b);

ARRAYS_IMEX PyObject *python_tuple(PyObject *o1, PyObject *o2);
ARRAYS_IMEX PyObject *python_tuple(PyObject *o1, PyObject *o2, PyObject *o3);
ARRAYS_IMEX PyObject *python_tuple(PyObject *o1, PyObject *o2, PyObject *o3, PyObject *a4);
ARRAYS_IMEX PyObject *python_tuple(PyObject *o1, PyObject *o2, PyObject *o3, PyObject *a4, PyObject *a5);

#endif
