"""ctypes bindings for the C money and IBAN library (build/libledgermoney).

Structure layouts and constants mirror c/include/lk_money.h and c/include/lk_iban.h. The library exports
lk_money_sizeof / lk_iban_info_sizeof so tests can detect layout drift between the two sides.
"""
import ctypes
import os
import pathlib
import sys

ROUND_HALF_UP = 0
ROUND_HALF_EVEN = 1
ROUND_DOWN = 2
ROUND_UP = 3

OK = 0
ERR_OVERFLOW = -1
ERR_DIV_ZERO = -2
ERR_CURRENCY = -3
ERR_ARG = -4
ERR_MODE = -5
ERR_IBAN_FORMAT = -6
ERR_IBAN_COUNTRY = -7
ERR_IBAN_LENGTH = -8
ERR_IBAN_CHECK = -9

ERROR_NAMES = {
    ERR_OVERFLOW: "overflow",
    ERR_DIV_ZERO: "division by zero",
    ERR_CURRENCY: "currency mismatch",
    ERR_ARG: "invalid argument",
    ERR_MODE: "unknown rounding mode",
    ERR_IBAN_FORMAT: "malformed IBAN",
    ERR_IBAN_COUNTRY: "unsupported IBAN country",
    ERR_IBAN_LENGTH: "wrong IBAN length",
    ERR_IBAN_CHECK: "IBAN checksum mismatch",
}

ROOT = pathlib.Path(__file__).resolve().parent.parent


class NativeError(Exception):
    """A negative status code returned by the C library."""

    def __init__(self, code):
        self.code = code
        super().__init__(f"{ERROR_NAMES.get(code, 'native error')} ({code})")


class LkMoney(ctypes.Structure):
    _fields_ = [
        ("minor", ctypes.c_int64),
        ("exponent", ctypes.c_int32),
        ("currency", ctypes.c_char * 4),
    ]


class LkIbanInfo(ctypes.Structure):
    _fields_ = [
        ("country", ctypes.c_char * 4),
        ("check_digits", ctypes.c_int32),
        ("length", ctypes.c_int32),
        ("expected_length", ctypes.c_int32),
    ]


def library_path():
    override = os.environ.get("LEDGERKIT_LIB")
    if override:
        return pathlib.Path(override)
    ext = "dylib" if sys.platform == "darwin" else "so"
    return ROOT / "build" / f"libledgermoney.{ext}"


_LIB = None


def _declare(lib):
    i64, i32, cp = ctypes.c_int64, ctypes.c_int32, ctypes.c_char_p
    pm, pi64 = ctypes.POINTER(LkMoney), ctypes.POINTER(ctypes.c_int64)
    specs = {
        "lk_money_sizeof": ([], ctypes.c_size_t),
        "lk_iban_info_sizeof": ([], ctypes.c_size_t),
        "lk_round_div": ([i64, i64, i32, pi64], ctypes.c_int),
        "lk_add_checked": ([i64, i64, pi64], ctypes.c_int),
        "lk_mul_checked": ([i64, i64, pi64], ctypes.c_int),
        "lk_currency_valid": ([cp], ctypes.c_int),
        "lk_money_make": ([pm, i64, i32, cp], ctypes.c_int),
        "lk_money_add": ([pm, pm, pm], ctypes.c_int),
        "lk_money_sub": ([pm, pm, pm], ctypes.c_int),
        "lk_money_mul_int": ([pm, i64, pm], ctypes.c_int),
        "lk_money_percent_bp": ([pm, i32, i32, pm], ctypes.c_int),
        "lk_money_cmp": ([pm, pm, ctypes.POINTER(i32)], ctypes.c_int),
        "lk_money_convert": ([pm, i64, cp, i32, i32, pm], ctypes.c_int),
        "lk_fee_minor": ([i64, i32], i64),
        "lk_iban_expected_length": ([cp], ctypes.c_int),
        "lk_iban_mod97": ([cp], ctypes.c_int),
        "lk_iban_validate": ([cp], ctypes.c_int),
        "lk_iban_check_digits": ([cp, cp, ctypes.c_char_p], ctypes.c_int),
        "lk_iban_parse": ([cp, ctypes.POINTER(LkIbanInfo)], ctypes.c_int),
    }
    for name, (argtypes, restype) in specs.items():
        fn = getattr(lib, name)
        fn.argtypes = argtypes
        fn.restype = restype
    return lib


def library():
    """Load the shared library once; raises OSError if `make build` has not run."""
    global _LIB
    if _LIB is None:
        _LIB = _declare(ctypes.CDLL(str(library_path())))
    return _LIB


def _check(rc):
    if rc < 0:
        raise NativeError(rc)
    return rc


def money_sizeof():
    return library().lk_money_sizeof()


def iban_info_sizeof():
    return library().lk_iban_info_sizeof()


def make_money(minor, exponent, currency):
    out = LkMoney()
    _check(library().lk_money_make(ctypes.byref(out), minor, exponent, currency.encode("ascii")))
    return out


def as_tuple(m):
    return (m.minor, m.exponent, m.currency.decode("ascii"))


def _binary(fn_name, a, b):
    out = LkMoney()
    fn = getattr(library(), fn_name)
    _check(fn(ctypes.byref(make_money(*a)), ctypes.byref(make_money(*b)), ctypes.byref(out)))
    return as_tuple(out)


def money_add(a, b):
    """Add two (minor, exponent, currency) tuples with overflow and currency checks."""
    return _binary("lk_money_add", a, b)


def money_sub(a, b):
    return _binary("lk_money_sub", a, b)


def money_cmp(a, b):
    result = ctypes.c_int32()
    _check(library().lk_money_cmp(ctypes.byref(make_money(*a)), ctypes.byref(make_money(*b)), ctypes.byref(result)))
    return result.value


def money_mul_int(a, k):
    out = LkMoney()
    _check(library().lk_money_mul_int(ctypes.byref(make_money(*a)), k, ctypes.byref(out)))
    return as_tuple(out)


def money_percent_bp(a, bp, mode=ROUND_HALF_UP):
    out = LkMoney()
    _check(library().lk_money_percent_bp(ctypes.byref(make_money(*a)), bp, mode, ctypes.byref(out)))
    return as_tuple(out)


def money_convert(a, rate_micro, to_currency, to_exponent, mode=ROUND_HALF_UP):
    out = LkMoney()
    _check(library().lk_money_convert(ctypes.byref(make_money(*a)), rate_micro, to_currency.encode("ascii"),
                                      to_exponent, mode, ctypes.byref(out)))
    return as_tuple(out)


def round_div(num, den, mode=ROUND_HALF_UP):
    out = ctypes.c_int64()
    _check(library().lk_round_div(num, den, mode, ctypes.byref(out)))
    return out.value


def add_checked(a, b):
    out = ctypes.c_int64()
    _check(library().lk_add_checked(a, b, ctypes.byref(out)))
    return out.value


def mul_checked(a, b):
    out = ctypes.c_int64()
    _check(library().lk_mul_checked(a, b, ctypes.byref(out)))
    return out.value


def fee_minor(minor, bp):
    """Proportional fee in minor units: minor * bp / 10000, rounded half up."""
    return _check(library().lk_fee_minor(minor, bp))


def iban_mod97(iban):
    return _check(library().lk_iban_mod97(iban.encode("ascii")))


def iban_status(iban):
    """Raw status of lk_iban_validate: 0 when valid, a negative code otherwise."""
    return library().lk_iban_validate(iban.encode("ascii"))


def iban_check_digits(country, bban):
    buf = ctypes.create_string_buffer(3)
    _check(library().lk_iban_check_digits(country.encode("ascii"), bban.encode("ascii"), buf))
    return buf.value.decode("ascii")


def iban_expected_length(country):
    return _check(library().lk_iban_expected_length(country.encode("ascii")))


def iban_parse(iban):
    info = LkIbanInfo()
    _check(library().lk_iban_parse(iban.encode("ascii"), ctypes.byref(info)))
    return {
        "country": info.country.decode("ascii"),
        "check_digits": info.check_digits,
        "length": info.length,
        "expected_length": info.expected_length,
    }
