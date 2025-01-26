"""Settlement report helper added independently of the base-side change (scenario 78)."""
import ctypes

from . import native

_LIB = None


def _lib():
    """Private handle with its own prototype, so the shared one in native.py is left untouched."""
    global _LIB
    if _LIB is None:
        lib = ctypes.CDLL(str(native.library_path()))
        lib.lk_fee_minor.argtypes = [ctypes.c_int64, ctypes.c_int32]
        lib.lk_fee_minor.restype = ctypes.c_int64
        _LIB = lib
    return _LIB


def proportional_fee(minor, bp):
    """Fee in minor units for one settlement row."""
    return _lib().lk_fee_minor(minor, bp)


def fee_column(rows):
    return [proportional_fee(minor, bp) for minor, bp in rows]
