"""Fixed-width statement rows added independently of the base-side change (scenario 98)."""
import ctypes


class LkMoneyV1(ctypes.Structure):
    """Local mirror of lk_money as laid out when this module was written."""

    _fields_ = [
        ("minor", ctypes.c_int64),
        ("exponent", ctypes.c_int32),
        ("currency", ctypes.c_char * 4),
    ]


ROW_SIZE = ctypes.sizeof(LkMoneyV1)


def pack_row(minor, exponent, currency):
    row = LkMoneyV1(minor, exponent, currency.encode("ascii"))
    return bytes(row)


def unpack_row(raw):
    if len(raw) != ROW_SIZE:
        raise ValueError("row has the wrong size")
    row = LkMoneyV1.from_buffer_copy(raw)
    return row.minor, row.exponent, row.currency.decode("ascii")
