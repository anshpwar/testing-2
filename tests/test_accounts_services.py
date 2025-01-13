import datetime as dt

from django.test import TestCase

from accounts import services
from accounts.models import Account, Customer
from ledgerkit import rules
from ledgerkit.money import Money

BBAN = "370400440532013000"
TODAY = dt.date(2025, 3, 1)


class AccountServiceTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(name="Test Customer", country="DE", created_on=dt.date(2024, 9, 1))

    def open(self, opened_on=dt.date(2025, 2, 20), bban=BBAN):
        return services.open_account(self.customer, bban, "EUR", opened_on)

    def test_open_account_generates_a_valid_iban(self):
        account = self.open()
        self.assertEqual(account.iban, "DE89370400440532013000")
        self.assertEqual(account.balance_minor, 0)
        self.assertEqual(account.status, Account.ACTIVE)

    def test_duplicate_iban_is_rejected(self):
        self.open()
        with self.assertRaises(services.AccountError):
            self.open()

    def test_age_and_tenure(self):
        account = self.open(opened_on=dt.date(2025, 2, 20))
        self.assertEqual(services.age_days(account, TODAY), 9)
        self.assertEqual(services.age_days(account, dt.date(2025, 1, 1)), 0)
        self.assertEqual(services.tenure_months(self.customer, TODAY), (TODAY - dt.date(2024, 9, 1)).days // 30)

    def test_limits_follow_policy_tables(self):
        account = self.open()
        age = services.age_days(account, TODAY)
        self.assertEqual(services.daily_limit(account, TODAY), Money(rules.daily_transfer_limit_cents(age), "EUR"))
        self.assertEqual(services.instant_cap(account, TODAY), Money(rules.instant_payment_cap_cents(age), "EUR"))
        months = services.tenure_months(self.customer, TODAY)
        self.assertEqual(services.overdraft_limit(account, TODAY), Money(rules.overdraft_limit_cents(months), "EUR"))

    def test_dormancy_uses_last_activity(self):
        account = self.open(opened_on=dt.date(2020, 1, 1))
        account.last_activity_on = TODAY - dt.timedelta(days=rules.dormancy_days(0))
        self.assertFalse(services.is_dormant(account, TODAY))
        account.last_activity_on = TODAY - dt.timedelta(days=rules.dormancy_days(0) + 1)
        self.assertTrue(services.is_dormant(account, TODAY))

    def test_failed_logins_escalate(self):
        for attempt in range(1, 8):
            self.assertEqual(services.register_failed_login(self.customer), rules.failed_login_lockout_s(attempt))
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.failed_logins, 7)

    def test_lookup_normalises_and_validates(self):
        account = self.open()
        self.assertEqual(services.lookup("de89 3704 0044 0532 0130 00"), account)
        with self.assertRaises(services.AccountError):
            services.lookup("DE88370400440532013000")
        with self.assertRaises(services.AccountError):
            services.lookup("GB82WEST12345698765432")

    def test_freeze(self):
        account = services.freeze(self.open())
        account.refresh_from_db()
        self.assertEqual(account.status, Account.FROZEN)

    def test_customers_in_class(self):
        Customer.objects.create(name="Second", risk_class=3, created_on=TODAY)
        self.assertEqual(list(services.customers_in_class(3).values_list("name", flat=True)), ["Second"])
