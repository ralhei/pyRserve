# -*- coding: utf-8 -*-
"""
Smoke tests that verify numpy >= 2.0 is installed and that the specific
APIs used by pyRserve work as expected under numpy 2.0 semantics.

These tests require no live Rserve connection.
"""
import struct

import numpy
import pytest


# ---------------------------------------------------------------------------
# Version guard
# ---------------------------------------------------------------------------

def test_numpy_version():
    """numpy >= 2.0 is required; catches accidental downgrades in CI."""
    major, minor = (int(x) for x in numpy.__version__.split('.')[:2])
    assert (major, minor) >= (2, 0), (
        "numpy >= 2.0 required, got %s" % numpy.__version__
    )


# ---------------------------------------------------------------------------
# Removed aliases must be absent
# ---------------------------------------------------------------------------

def test_string_alias_removed():
    """numpy.string_ was removed in 2.0 (replaced by numpy.bytes_)."""
    assert not hasattr(numpy, 'string_'), (
        "numpy.string_ still exists — downgrade to numpy < 2.0?"
    )


def test_compat_module_removed():
    """numpy.compat (and numpy.compat.long) was removed in 2.0."""
    assert not hasattr(numpy, 'compat'), (
        "numpy.compat still exists — downgrade to numpy < 2.0?"
    )


def test_unicode_alias_removed():
    """numpy.unicode_ was removed in 2.0 (replaced by numpy.str_)."""
    assert not hasattr(numpy, 'unicode_'), (
        "numpy.unicode_ still exists — downgrade to numpy < 2.0?"
    )


# ---------------------------------------------------------------------------
# Replacement types must be present
# ---------------------------------------------------------------------------

def test_replacement_types_exist():
    """All scalar types used in rtypes.py / rparser.py after migration."""
    for name in ('bytes_', 'bool_', 'str_',
                 'int32', 'int64', 'float64', 'double', 'complex128'):
        assert hasattr(numpy, name), "numpy.%s missing" % name


# ---------------------------------------------------------------------------
# frombuffer with every dtype used in rparser.py
# ---------------------------------------------------------------------------

def test_frombuffer_bool():
    """xt_array_bool path: read numpy.bool_ from raw bytes."""
    raw = struct.pack('4B', 1, 0, 1, 1)
    arr = numpy.frombuffer(raw, dtype=numpy.bool_)
    assert arr.dtype == numpy.bool_
    assert list(arr) == [True, False, True, True]


def test_frombuffer_int8_for_bool_na():
    """bool-NA path: read int8 so that sentinel value 2 can be detected."""
    raw = struct.pack('4b', 1, 0, 2, 1)
    arr = numpy.frombuffer(raw, dtype=numpy.int8)
    assert arr.dtype == numpy.int8
    assert arr[2] == 2  # NA sentinel


def test_frombuffer_int32():
    """XT_ARRAY_INT path."""
    raw = struct.pack('<3i', -1, 0, 300)
    arr = numpy.frombuffer(raw, dtype=numpy.int32)
    assert arr.dtype == numpy.int32
    assert list(arr) == [-1, 0, 300]


def test_frombuffer_float64():
    """XT_ARRAY_DOUBLE path."""
    raw = struct.pack('<2d', 1.5, -3.14)
    arr = numpy.frombuffer(raw, dtype=numpy.float64)
    assert arr.dtype == numpy.float64
    assert abs(arr[1] - (-3.14)) < 1e-10


def test_frombuffer_complex128():
    """XT_ARRAY_CPLX path: pairs of doubles become complex128 values."""
    raw = struct.pack('<4d', 1.0, 2.0, -3.0, 4.0)
    arr = numpy.frombuffer(raw, dtype=numpy.complex128)
    assert arr.dtype == numpy.complex128
    assert arr[0] == complex(1.0, 2.0)
    assert arr[1] == complex(-3.0, 4.0)


# ---------------------------------------------------------------------------
# astype casts used in rparser.py and rserializer.py
# ---------------------------------------------------------------------------

def test_astype_int8_to_object_with_none_assignment():
    """
    rparser.py bool-NA path: int8 -> object array, then write None at
    positions where the NA sentinel (2) appears.
    """
    raw = struct.pack('4b', 1, 0, 2, 1)
    arr = numpy.frombuffer(raw, dtype=numpy.int8).astype(object)
    arr[arr == 2] = None
    assert arr[0] == 1
    assert arr[1] == 0
    assert arr[2] is None
    assert arr[3] == 1


def test_astype_int64_to_int32():
    """rserializer.py downcasts int64 arrays whose values fit in int32."""
    arr64 = numpy.array([1, -2, 300], dtype=numpy.int64)
    arr32 = arr64.astype(numpy.int32)
    assert arr32.dtype == numpy.int32
    assert list(arr32) == [1, -2, 300]


# ---------------------------------------------------------------------------
# Array serialisation helpers (tobytes / reshape in Fortran order)
# ---------------------------------------------------------------------------

def test_tobytes_fortran_order():
    """rserializer.py writes arrays in column-major (Fortran) byte order."""
    arr = numpy.array([[1, 2, 3], [4, 5, 6]], dtype=numpy.int32)
    b = arr.tobytes(order='F')
    # column-major: [1,4], [2,5], [3,6]
    assert b == struct.pack('<6i', 1, 4, 2, 5, 3, 6)


def test_reshape_fortran_order():
    """rparser.py reconstructs multi-dim arrays sent in Fortran order."""
    flat = numpy.array([1, 4, 2, 5, 3, 6], dtype=numpy.int32)
    arr = flat.reshape((2, 3), order='F')
    assert arr.shape == (2, 3)
    assert arr[0, 0] == 1 and arr[1, 0] == 4  # first column
    assert arr[0, 1] == 2 and arr[1, 1] == 5  # second column


# ---------------------------------------------------------------------------
# numpy.bytes_ replacing numpy.string_
# ---------------------------------------------------------------------------

def test_bytes_scalar_isinstance():
    """numpy.bytes_ is usable for isinstance checks (replaces numpy.string_)."""
    arr = numpy.array([b'hello', b'world'])
    assert issubclass(arr.dtype.type, numpy.bytes_)
    assert isinstance(arr[0], numpy.bytes_)


def test_bytes_in_numpymap_lookup():
    """dtype.type of a bytes array resolves to numpy.bytes_ (used in numpyMap)."""
    arr = numpy.array([b'abc'])
    assert arr.dtype.type is numpy.bytes_


# ---------------------------------------------------------------------------
# numpy 2.0 casting strictness: arange with float stop + integer dtype
# ---------------------------------------------------------------------------

def test_arange_integer_stop_works():
    """The fixed pattern in test_rparser.py (integer division) must not raise."""
    arr = numpy.arange(10, dtype=numpy.int32)
    assert arr.dtype == numpy.int32
    assert len(arr) == 10


def test_ufunc_out_same_kind_casting():
    """
    numpy 2.0 changed the default ufunc out= casting from 'unsafe' to
    'same_kind'.  Writing a float result into an integer out= array now
    raises TypeError instead of silently truncating.
    """
    a = numpy.array([1.5])
    out = numpy.array([0], dtype=numpy.int32)
    with pytest.raises(TypeError):
        numpy.add(a, 1.0, out=out)
