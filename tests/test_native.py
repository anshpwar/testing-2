import ctypes
import pathlib
import re
import unittest

from ledgerkit import native

HEADER = pathlib.Path(__file__).resolve().parent.parent / "c" / "include" / "lk_money.h"


def header_constants():
    return {m.group(1): int(m.group(2)) for m in re.finditer(r"#define (LK_\w+) \(?(-?\d+)\)?", HEADER.read_text())}


class LayoutTests(unittest.TestCase):
    def test_money_layout_size(self):
        self.assertEqual(native.money_sizeof(), 24)
        self.assertEqual(ctypes.sizeof(native.LkMoney), 24)

    def test_money_layout_matches_library(self):
        self.assertEqual(ctypes.sizeof(native.LkMoney), native.money_sizeof())

    def test_money_flags_start_clear(self):
        self.assertEqual(native.make_money(1, 2, "EUR").flags, 0)

    def test_iban_info_layout_matches_library(self):
        self.assertEqual(ctypes.sizeof(native.LkIbanInfo), native.iban_info_sizeof())

    def test_error_codes_mirror_header(self):
        consts = header_constants()
        self.assertEqual(consts["LK_ERR_OVERFLOW"], native.ERR_OVERFLOW)
        self.assertEqual(consts["LK_ERR_CURRENCY"], native.ERR_CURRENCY)
        self.assertEqual(consts["LK_ERR_MODE"], native.ERR_MODE)
        self.assertEqual(consts["LK_ERR_IBAN_CHECK"], native.ERR_IBAN_CHECK)

    def test_rounding_modes_mirror_header(self):
        consts = header_constants()
        self.assertEqual(consts["LK_ROUND_HALF_UP"], native.ROUND_HALF_UP)
        self.assertEqual(consts["LK_ROUND_HALF_EVEN"], native.ROUND_HALF_EVEN)
        self.assertEqual(consts["LK_ROUND_DOWN"], native.ROUND_DOWN)
        self.assertEqual(consts["LK_ROUND_UP"], native.ROUND_UP)


class ArithmeticTests(unittest.TestCase):
    def test_make_and_roundtrip(self):
        m = native.make_money(1050, 2, "EUR")
        self.assertEqual(native.as_tuple(m), (1050, 2, "EUR"))

    def test_make_rejects_bad_currency(self):
        with self.assertRaises(native.NativeError) as ctx:
            native.make_money(1, 2, "eur")
        self.assertEqual(ctx.exception.code, native.ERR_CURRENCY)

    def test_add_and_sub(self):
        self.assertEqual(native.money_add((1050, 2, "EUR"), (295, 2, "EUR")), (1345, 2, "EUR"))
        self.assertEqual(native.money_sub((295, 2, "EUR"), (1050, 2, "EUR")), (-755, 2, "EUR"))

    def test_add_overflow_is_an_error_not_a_wrap(self):
        with self.assertRaises(native.NativeError) as ctx:
            native.money_add((2 ** 63 - 1, 2, "EUR"), (1, 2, "EUR"))
        self.assertEqual(ctx.exception.code, native.ERR_OVERFLOW)

    def test_currency_mismatch(self):
        with self.assertRaises(native.NativeError) as ctx:
            native.money_add((1, 2, "EUR"), (1, 2, "USD"))
        self.assertEqual(ctx.exception.code, native.ERR_CURRENCY)

    def test_cmp(self):
        self.assertEqual(native.money_cmp((5, 2, "EUR"), (7, 2, "EUR")), -1)
        self.assertEqual(native.money_cmp((7, 2, "EUR"), (7, 2, "EUR")), 0)

    def test_checked_primitives(self):
        self.assertEqual(native.add_checked(40, 2), 42)
        self.assertEqual(native.mul_checked(-6, 7), -42)
        with self.assertRaises(native.NativeError):
            native.mul_checked(2 ** 62, 4)

    def test_percent_bp_modes(self):
        self.assertEqual(native.money_percent_bp((295, 2, "EUR"), 50, native.ROUND_UP)[0], 2)
        self.assertEqual(native.money_percent_bp((295, 2, "EUR"), 50, native.ROUND_DOWN)[0], 1)

    def test_convert_between_exponents(self):
        self.assertEqual(native.money_convert((1050, 2, "EUR"), 1084500, "USD", 2), (1139, 2, "USD"))
        self.assertEqual(native.money_convert((1050, 2, "EUR"), 160250000, "JPY", 0, native.ROUND_HALF_EVEN), (1683, 0, "JPY"))


class RoundingTests(unittest.TestCase):
    def test_round_div_modes(self):
        self.assertEqual(native.round_div(5, 2, native.ROUND_HALF_UP), 3)
        self.assertEqual(native.round_div(5, 2, native.ROUND_HALF_EVEN), 2)
        self.assertEqual(native.round_div(-7, 3, native.ROUND_DOWN), -2)
        self.assertEqual(native.round_div(-7, 3, native.ROUND_UP), -3)

    def test_round_div_errors(self):
        with self.assertRaises(native.NativeError) as ctx:
            native.round_div(1, 0)
        self.assertEqual(ctx.exception.code, native.ERR_DIV_ZERO)
        with self.assertRaises(native.NativeError) as ctx:
            native.round_div(1, 3, 9)
        self.assertEqual(ctx.exception.code, native.ERR_MODE)

    def test_round_div_matches_python_floor_semantics_for_positive_values(self):
        for num in range(0, 200, 7):
            for den in (3, 8, 10, 97):
                self.assertEqual(native.round_div(num, den, native.ROUND_DOWN), num // den)


class FeeTests(unittest.TestCase):
    def test_fee_minor_half_up(self):
        self.assertEqual(native.fee_minor(10000, 250), 250)
        self.assertEqual(native.fee_minor(1999, 150), 30)

    def test_fee_minor_rejects_negative_amounts(self):
        with self.assertRaises(native.NativeError) as ctx:
            native.fee_minor(-1, 150)
        self.assertEqual(ctx.exception.code, native.ERR_ARG)


class IbanBindingTests(unittest.TestCase):
    def test_mod97_of_valid_iban_is_one(self):
        self.assertEqual(native.iban_mod97("GB82WEST12345698765432"), 1)

    def test_status_codes(self):
        self.assertEqual(native.iban_status("DE89370400440532013000"), native.OK)
        self.assertEqual(native.iban_status("DE88370400440532013000"), native.ERR_IBAN_CHECK)
        self.assertEqual(native.iban_status("XX89370400440532013000"), native.ERR_IBAN_COUNTRY)

    def test_check_digits_and_parse(self):
        self.assertEqual(native.iban_check_digits("NL", "ABNA0417164300"), "91")
        info = native.iban_parse("NL91ABNA0417164300")
        self.assertEqual(info, {"country": "NL", "check_digits": 91, "length": 18, "expected_length": 18})
