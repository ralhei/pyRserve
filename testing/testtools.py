"""
Some helper functions for unit testing
"""
from numpy import ndarray, float32, float64, complex64, complex128


def compareArrays(arr1, arr2):
    """Compare two (possibly nested) arrays"""
    def _compareArrays(xarr1, xarr2):
        assert xarr1.shape == xarr2.shape
        for idx in range(len(xarr1)):
            if isinstance(xarr1[idx], ndarray):
                _compareArrays(xarr1[idx], xarr2[idx])
            else:
                if type(xarr1[idx]) in [float, float32, float64, complex,
                                        complex64, complex128]:
                    # make a comparison which works for floats and complex
                    # numbers
                    assert abs(xarr1[idx] - xarr2[idx]) < 0.000001
                else:
                    assert xarr1[idx] == xarr2[idx]
    try:
        _compareArrays(arr1, arr2)
    except TypeError:
        return False
    return True
