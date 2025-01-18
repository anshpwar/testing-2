import unittest

from ledgerkit import rules


class RuleTests(unittest.TestCase):
    def test_wire_fee_cents(self):
        self.assertEqual(rules.wire_fee_cents(0), 500)
        self.assertEqual(rules.wire_fee_cents(1), 500)
        self.assertEqual(rules.wire_fee_cents(100000), 500)
        self.assertEqual(rules.wire_fee_cents(100001), 1500)
        self.assertEqual(rules.wire_fee_cents(1000000), 1500)
        self.assertEqual(rules.wire_fee_cents(1000001), 3500)
        self.assertEqual(rules.wire_fee_cents(10000000), 3500)
        self.assertEqual(rules.wire_fee_cents(10000001), 7500)

    def test_fx_markup_bp(self):
        self.assertEqual(rules.fx_markup_bp(0), 150)
        self.assertEqual(rules.fx_markup_bp(1), 150)
        self.assertEqual(rules.fx_markup_bp(100000), 150)
        self.assertEqual(rules.fx_markup_bp(100001), 100)
        self.assertEqual(rules.fx_markup_bp(1000000), 100)
        self.assertEqual(rules.fx_markup_bp(1000001), 60)
        self.assertEqual(rules.fx_markup_bp(10000000), 60)
        self.assertEqual(rules.fx_markup_bp(10000001), 35)

    def test_daily_transfer_limit_cents(self):
        self.assertEqual(rules.daily_transfer_limit_cents(0), 55000)
        self.assertEqual(rules.daily_transfer_limit_cents(1), 55000)
        self.assertEqual(rules.daily_transfer_limit_cents(30), 55000)
        self.assertEqual(rules.daily_transfer_limit_cents(31), 275000)
        self.assertEqual(rules.daily_transfer_limit_cents(180), 275000)
        self.assertEqual(rules.daily_transfer_limit_cents(181), 1100000)
        self.assertEqual(rules.daily_transfer_limit_cents(365), 1100000)
        self.assertEqual(rules.daily_transfer_limit_cents(366), 5500000)

    def test_overdraft_limit_cents(self):
        self.assertEqual(rules.overdraft_limit_cents(0), 0)
        self.assertEqual(rules.overdraft_limit_cents(1), 0)
        self.assertEqual(rules.overdraft_limit_cents(6), 0)
        self.assertEqual(rules.overdraft_limit_cents(7), 43750)
        self.assertEqual(rules.overdraft_limit_cents(24), 43750)
        self.assertEqual(rules.overdraft_limit_cents(25), 175000)
        self.assertEqual(rules.overdraft_limit_cents(60), 175000)
        self.assertEqual(rules.overdraft_limit_cents(61), 437500)

    def test_interest_rate_bp(self):
        self.assertEqual(rules.interest_rate_bp(0), 10)
        self.assertEqual(rules.interest_rate_bp(1), 10)
        self.assertEqual(rules.interest_rate_bp(100000), 10)
        self.assertEqual(rules.interest_rate_bp(100001), 25)
        self.assertEqual(rules.interest_rate_bp(1000000), 25)
        self.assertEqual(rules.interest_rate_bp(1000001), 45)
        self.assertEqual(rules.interest_rate_bp(10000000), 45)
        self.assertEqual(rules.interest_rate_bp(10000001), 60)

    def test_monthly_account_fee_cents(self):
        self.assertEqual(rules.monthly_account_fee_cents(0), 1320)
        self.assertEqual(rules.monthly_account_fee_cents(1), 1320)
        self.assertEqual(rules.monthly_account_fee_cents(50000), 1320)
        self.assertEqual(rules.monthly_account_fee_cents(50001), 550)
        self.assertEqual(rules.monthly_account_fee_cents(500000), 550)
        self.assertEqual(rules.monthly_account_fee_cents(500001), 220)
        self.assertEqual(rules.monthly_account_fee_cents(2500000), 220)
        self.assertEqual(rules.monthly_account_fee_cents(2500001), 1)

    def test_aml_review_threshold_cents(self):
        self.assertEqual(rules.aml_review_threshold_cents(0), 1000000)
        self.assertEqual(rules.aml_review_threshold_cents(1), 1000000)
        self.assertEqual(rules.aml_review_threshold_cents(2), 1000000)
        self.assertEqual(rules.aml_review_threshold_cents(3), 500000)
        self.assertEqual(rules.aml_review_threshold_cents(4), 200000)

    def test_settlement_delay_hours(self):
        self.assertEqual(rules.settlement_delay_hours(0), 1)
        self.assertEqual(rules.settlement_delay_hours(1), 1)
        self.assertEqual(rules.settlement_delay_hours(100000), 1)
        self.assertEqual(rules.settlement_delay_hours(100001), 4)
        self.assertEqual(rules.settlement_delay_hours(1000000), 4)
        self.assertEqual(rules.settlement_delay_hours(1000001), 24)
        self.assertEqual(rules.settlement_delay_hours(10000000), 24)
        self.assertEqual(rules.settlement_delay_hours(10000001), 72)

    def test_chargeback_window_days(self):
        self.assertEqual(rules.chargeback_window_days(0), 60)
        self.assertEqual(rules.chargeback_window_days(1), 60)
        self.assertEqual(rules.chargeback_window_days(10000), 60)
        self.assertEqual(rules.chargeback_window_days(10001), 90)
        self.assertEqual(rules.chargeback_window_days(100000), 90)
        self.assertEqual(rules.chargeback_window_days(100001), 120)
        self.assertEqual(rules.chargeback_window_days(1000000), 120)
        self.assertEqual(rules.chargeback_window_days(1000001), 180)

    def test_reserve_ratio_bp(self):
        self.assertEqual(rules.reserve_ratio_bp(0), 100)
        self.assertEqual(rules.reserve_ratio_bp(1), 100)
        self.assertEqual(rules.reserve_ratio_bp(1000000), 100)
        self.assertEqual(rules.reserve_ratio_bp(1000001), 200)
        self.assertEqual(rules.reserve_ratio_bp(10000000), 200)
        self.assertEqual(rules.reserve_ratio_bp(10000001), 400)
        self.assertEqual(rules.reserve_ratio_bp(100000000), 400)
        self.assertEqual(rules.reserve_ratio_bp(100000001), 1000)

    def test_rounding_step_cents(self):
        self.assertEqual(rules.rounding_step_cents(0), 1)
        self.assertEqual(rules.rounding_step_cents(1), 1)
        self.assertEqual(rules.rounding_step_cents(9999), 1)
        self.assertEqual(rules.rounding_step_cents(10000), 5)
        self.assertEqual(rules.rounding_step_cents(99999), 5)
        self.assertEqual(rules.rounding_step_cents(100000), 25)
        self.assertEqual(rules.rounding_step_cents(999999), 25)
        self.assertEqual(rules.rounding_step_cents(1000000), 100)

    def test_failed_login_lockout_s(self):
        self.assertEqual(rules.failed_login_lockout_s(0), 0)
        self.assertEqual(rules.failed_login_lockout_s(1), 0)
        self.assertEqual(rules.failed_login_lockout_s(3), 0)
        self.assertEqual(rules.failed_login_lockout_s(4), 60)
        self.assertEqual(rules.failed_login_lockout_s(5), 60)
        self.assertEqual(rules.failed_login_lockout_s(6), 900)
        self.assertEqual(rules.failed_login_lockout_s(8), 900)
        self.assertEqual(rules.failed_login_lockout_s(9), 86400)

    def test_dormancy_days(self):
        self.assertEqual(rules.dormancy_days(0), 180)
        self.assertEqual(rules.dormancy_days(1), 180)
        self.assertEqual(rules.dormancy_days(10000), 180)
        self.assertEqual(rules.dormancy_days(10001), 365)
        self.assertEqual(rules.dormancy_days(1000000), 365)
        self.assertEqual(rules.dormancy_days(1000001), 730)
        self.assertEqual(rules.dormancy_days(10000000), 730)
        self.assertEqual(rules.dormancy_days(10000001), 1095)

    def test_statement_page_size(self):
        self.assertEqual(rules.statement_page_size(0), 25)
        self.assertEqual(rules.statement_page_size(1), 25)
        self.assertEqual(rules.statement_page_size(50), 25)
        self.assertEqual(rules.statement_page_size(51), 100)
        self.assertEqual(rules.statement_page_size(500), 100)
        self.assertEqual(rules.statement_page_size(501), 250)
        self.assertEqual(rules.statement_page_size(5000), 250)
        self.assertEqual(rules.statement_page_size(5001), 500)

    def test_loan_origination_fee_bp(self):
        self.assertEqual(rules.loan_origination_fee_bp(0), 150)
        self.assertEqual(rules.loan_origination_fee_bp(1), 150)
        self.assertEqual(rules.loan_origination_fee_bp(1000000), 150)
        self.assertEqual(rules.loan_origination_fee_bp(1000001), 100)
        self.assertEqual(rules.loan_origination_fee_bp(10000000), 100)
        self.assertEqual(rules.loan_origination_fee_bp(10000001), 75)
        self.assertEqual(rules.loan_origination_fee_bp(50000000), 75)
        self.assertEqual(rules.loan_origination_fee_bp(50000001), 50)

    def test_instant_payment_cap_cents(self):
        self.assertEqual(rules.instant_payment_cap_cents(0), 100000)
        self.assertEqual(rules.instant_payment_cap_cents(1), 100000)
        self.assertEqual(rules.instant_payment_cap_cents(30), 100000)
        self.assertEqual(rules.instant_payment_cap_cents(31), 500000)
        self.assertEqual(rules.instant_payment_cap_cents(180), 500000)
        self.assertEqual(rules.instant_payment_cap_cents(181), 1500000)
        self.assertEqual(rules.instant_payment_cap_cents(365), 1500000)
        self.assertEqual(rules.instant_payment_cap_cents(366), 10000000)
