import unittest

from ledgerkit import fees, rules
from ledgerkit.money import Money

AMOUNTS = [0, 1, 99999, 100000, 100001, 999999, 1000001, 12345678]


def half_up(num, den):
    return (2 * num + den) // (2 * den)


class FeeTests(unittest.TestCase):
    def test_wire_fee_follows_policy_table(self):
        for x in AMOUNTS:
            self.assertEqual(fees.wire_fee(Money(x, "EUR")), Money(rules.wire_fee_cents(x), "EUR"))

    def test_wire_fee_ignores_sign(self):
        self.assertEqual(fees.wire_fee(Money(-5000, "EUR")), fees.wire_fee(Money(5000, "EUR")))

    def test_fx_markup_is_proportional(self):
        for x in AMOUNTS:
            bp = rules.fx_markup_bp(x)
            self.assertEqual(fees.fx_markup(Money(x, "USD")).minor, half_up(x * bp, 10000))

    def test_transfer_cost_adds_markup_only_across_currencies(self):
        amount = Money(250000, "EUR")
        self.assertEqual(fees.transfer_cost(amount), fees.wire_fee(amount))
        self.assertEqual(fees.transfer_cost(amount, cross_currency=True), fees.wire_fee(amount) + fees.fx_markup(amount))

    def test_monthly_fee_ignores_negative_balance(self):
        self.assertEqual(fees.monthly_account_fee(Money(-500, "EUR")).minor, rules.monthly_account_fee_cents(0))
        for x in (0, 50000, 50001, 3000000):
            self.assertEqual(fees.monthly_account_fee(Money(x, "EUR")).minor, rules.monthly_account_fee_cents(x))

    def test_loan_origination_fee(self):
        for x in (500000, 5000000, 20000000, 90000000):
            bp = rules.loan_origination_fee_bp(x)
            self.assertEqual(fees.loan_origination_fee(Money(x, "EUR")).minor, half_up(x * bp, 10000))

    def test_round_for_display_lands_on_the_step(self):
        for x in (1, 4321, 123456, 7777777):
            step = rules.rounding_step_cents(x)
            rounded = fees.round_for_display(Money(x, "EUR"))
            self.assertEqual(rounded.minor % step, 0)
            self.assertLessEqual(abs(rounded.minor - x) * 2, step)
