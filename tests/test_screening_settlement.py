import datetime as dt
import unittest

from ledgerkit import rules, screening, settlement
from ledgerkit.money import Money


class ScreeningTests(unittest.TestCase):
    def test_threshold_is_inclusive(self):
        for risk in (1, 2, 3, 4):
            limit = rules.aml_review_threshold_cents(risk)
            self.assertTrue(screening.screen(Money(limit, "EUR"), risk).review)
            self.assertFalse(screening.screen(Money(limit - 1, "EUR"), risk).review)

    def test_high_risk_country_is_always_reviewed(self):
        decision = screening.screen(Money(1, "EUR"), 1, "KP")
        self.assertTrue(decision.review)
        self.assertIn("high-risk", decision.reason)

    def test_clear_decision(self):
        self.assertEqual(screening.screen(Money(1, "EUR"), 1, "DE"), screening.Decision(False, "clear"))

    def test_review_threshold_money(self):
        self.assertEqual(screening.review_threshold(2), Money(rules.aml_review_threshold_cents(2), "EUR"))

    def test_login_lockout(self):
        for attempts in (1, 3, 4, 5, 6, 9):
            self.assertEqual(screening.login_lockout_seconds(attempts), rules.failed_login_lockout_s(attempts))


class SettlementTests(unittest.TestCase):
    def test_settlement_time(self):
        booked = dt.datetime(2025, 2, 3, 10, 0)
        for x in (500, 500000, 5000000, 50000000):
            hours = rules.settlement_delay_hours(x)
            self.assertEqual(settlement.settles_at(booked, Money(x, "EUR")), booked + dt.timedelta(hours=hours))

    def test_chargeback_deadline(self):
        booked = dt.date(2025, 2, 3)
        for x in (500, 50000, 500000, 5000000):
            self.assertEqual(settlement.chargeback_deadline(booked, Money(x, "EUR")),
                             booked + dt.timedelta(days=rules.chargeback_window_days(x)))

    def test_limits_scale_with_age(self):
        for age in (0, 30, 31, 200, 400):
            self.assertEqual(settlement.daily_limit(age).minor, rules.daily_transfer_limit_cents(age))
            self.assertEqual(settlement.instant_cap(age, "USD"), Money(rules.instant_payment_cap_cents(age), "USD"))

    def test_overdraft_by_tenure(self):
        for months in (0, 6, 7, 30, 120):
            self.assertEqual(settlement.overdraft_limit(months).minor, rules.overdraft_limit_cents(months))

    def test_reserve_required(self):
        for deposits in (500000, 5000000, 50000000, 500000000):
            bp = rules.reserve_ratio_bp(deposits)
            self.assertEqual(settlement.reserve_required(Money(deposits, "EUR")).minor, (2 * deposits * bp + 10000) // 20000)

    def test_page_size(self):
        for n in (0, 50, 51, 600):
            self.assertEqual(settlement.page_size(n), rules.statement_page_size(n))
