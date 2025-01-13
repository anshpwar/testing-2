import unittest

from ledgerkit import native
from ledgerkit.money import CurrencyError, Money


class MoneyTests(unittest.TestCase):
    def test_parse_and_format(self):
        self.assertEqual(Money.parse("12.3", "EUR"), Money(1230, "EUR"))
        self.assertEqual(Money.parse("-0.05", "USD"), Money(-5, "USD"))
        self.assertEqual(Money.parse("1500", "JPY"), Money(1500, "JPY"))
        self.assertEqual(Money(123456789, "EUR").format(), "1,234,567.89 EUR")
        self.assertEqual(Money(-5, "EUR").format(), "-0.05 EUR")
        self.assertEqual(Money(1500, "JPY").format(), "1,500 JPY")
        self.assertEqual(Money(12345, "KWD").format(), "12.345 KWD")

    def test_parse_rejects_extra_precision_and_garbage(self):
        with self.assertRaises(ValueError):
            Money.parse("12.345", "EUR")
        with self.assertRaises(ValueError):
            Money.parse("12.5", "JPY")
        with self.assertRaises(ValueError):
            Money.parse("abc", "EUR")

    def test_unknown_currency(self):
        with self.assertRaises(CurrencyError):
            Money(1, "XXX")

    def test_arithmetic(self):
        a, b = Money(1050, "EUR"), Money(295, "EUR")
        self.assertEqual(a + b, Money(1345, "EUR"))
        self.assertEqual(b - a, Money(-755, "EUR"))
        self.assertEqual(-a, Money(-1050, "EUR"))
        self.assertEqual(a * 3, Money(3150, "EUR"))
        self.assertEqual(3 * a, Money(3150, "EUR"))

    def test_comparison(self):
        a, b = Money(10, "EUR"), Money(20, "EUR")
        self.assertTrue(a < b and a <= b and b > a and b >= a)
        self.assertFalse(a > b)

    def test_mixed_currency_is_rejected_by_the_library(self):
        with self.assertRaises(native.NativeError) as ctx:
            Money(1, "EUR") + Money(1, "USD")
        self.assertEqual(ctx.exception.code, native.ERR_CURRENCY)
        with self.assertRaises(native.NativeError):
            Money(1, "EUR") < Money(1, "USD")

    def test_overflow_raises(self):
        with self.assertRaises(native.NativeError) as ctx:
            Money(2 ** 63 - 1, "EUR") + Money(1, "EUR")
        self.assertEqual(ctx.exception.code, native.ERR_OVERFLOW)

    def test_percent_bp(self):
        self.assertEqual(Money(1050, "EUR").percent_bp(250), Money(26, "EUR"))
        self.assertEqual(Money(295, "EUR").percent_bp(50, native.ROUND_UP), Money(2, "EUR"))

    def test_convert(self):
        self.assertEqual(Money(1050, "EUR").convert(1084500, "USD"), Money(1139, "USD"))
        self.assertEqual(Money(1050, "EUR").convert(160250000, "JPY"), Money(1683, "JPY"))

    def test_allocate_distributes_every_cent(self):
        parts = Money(100, "EUR").allocate([1, 1, 1])
        self.assertEqual([p.minor for p in parts], [34, 33, 33])
        self.assertEqual(sum(p.minor for p in Money(1001, "EUR").allocate([3, 5, 2])), 1001)
        self.assertEqual(sum(p.minor for p in Money(-7, "EUR").allocate([1, 2])), -7)

    def test_allocate_rejects_bad_ratios(self):
        with self.assertRaises(ValueError):
            Money(10, "EUR").allocate([0, 0])
        with self.assertRaises(ValueError):
            Money(10, "EUR").allocate([1, -1])
