import unittest
from fractions import Fraction

from ledgerkit import interest, rules
from ledgerkit.money import Money


def expected_interest(balance, days):
    yearly = balance * rules.interest_rate_bp(balance) // 10000
    return round(Fraction(yearly * days, 365))


class InterestTests(unittest.TestCase):
    def test_no_interest_on_empty_or_overdrawn_balances(self):
        self.assertEqual(interest.daily_interest(Money(0, "EUR")).minor, 0)
        self.assertEqual(interest.daily_interest(Money(-90000, "EUR"), 30).minor, 0)

    def test_interest_uses_policy_rate_and_bankers_rounding(self):
        for balance in (5000, 100000, 100001, 750000, 4000000, 25000000):
            for days in (1, 7, 30, 31):
                self.assertEqual(interest.daily_interest(Money(balance, "EUR"), days).minor,
                                 expected_interest(balance, days), (balance, days))

    def test_accrue_adds_interest(self):
        start = Money(4000000, "EUR")
        self.assertEqual(interest.accrue(start, 30), start + interest.daily_interest(start, 30))

    def test_annual_rate_comes_from_the_table(self):
        self.assertEqual(interest.annual_rate_bp(Money(50000, "EUR")), rules.interest_rate_bp(50000))
        self.assertEqual(interest.annual_rate_bp(Money(-1, "EUR")), rules.interest_rate_bp(0))

    def test_dormancy_boundary(self):
        for balance in (0, 20000, 2000000):
            limit = rules.dormancy_days(balance)
            self.assertFalse(interest.dormancy_charge_due(Money(balance, "EUR"), limit))
            self.assertTrue(interest.dormancy_charge_due(Money(balance, "EUR"), limit + 1))
