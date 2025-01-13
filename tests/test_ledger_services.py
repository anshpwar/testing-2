import datetime as dt
from unittest import mock

from django.test import TestCase

from accounts import services as account_services
from accounts.models import Customer
from ledger import services
from ledger.models import JournalEntry
from ledgerkit import fees, rules
from ledgerkit.money import Money

DAY = dt.date(2025, 3, 1)


class LedgerTestCase(TestCase):
    def make_account(self, name, bban, currency="EUR", balance=0, risk_class=1, opened_on=dt.date(2025, 2, 24),
                     created_on=dt.date(2025, 2, 1), country="DE"):
        customer = Customer.objects.create(name=name, country=country, risk_class=risk_class, created_on=created_on)
        account = account_services.open_account(customer, bban, currency, opened_on)
        account.balance_minor = balance
        account.save(update_fields=["balance_minor"])
        return account

    def setUp(self):
        self.alice = self.make_account("Alice", "370400440532013000", balance=10_000_000)
        self.bob = self.make_account("Bob", "500105170123456789", balance=0)
        self.limit = account_services.daily_limit(self.alice, DAY)

    def refresh(self, *accounts):
        for a in accounts:
            a.refresh_from_db()


class PostTransferTests(LedgerTestCase):
    def test_transfer_moves_money_and_charges_fee(self):
        amount = Money(self.limit.minor // 2, "EUR")
        entry = services.post_transfer(self.alice, self.bob, amount, DAY, "rent")
        self.refresh(self.alice, self.bob)
        fee = fees.wire_fee(amount)
        self.assertEqual(self.bob.balance_minor, amount.minor)
        self.assertEqual(self.alice.balance_minor, 10_000_000 - amount.minor - rules.wire_fee_cents(amount.minor))
        self.assertEqual(entry.kind, "transfer")
        self.assertEqual(entry.postings.count(), 2)
        self.assertEqual(JournalEntry.objects.filter(kind="fee").count(), 1 if fee.minor else 0)

    def test_books_stay_balanced(self):
        services.post_transfer(self.alice, self.bob, Money(self.limit.minor // 3, "EUR"), DAY)
        self.assertEqual(services.trial_balance("EUR"), 0)
        for account in (self.alice, self.bob):
            self.refresh(account)
            self.assertEqual(account.balance_minor - (10_000_000 if account is self.alice else 0),
                             services.balance_from_postings(account).minor)

    def test_daily_limit_is_enforced_across_transfers(self):
        first = Money(self.limit.minor - 10, "EUR")
        services.post_transfer(self.alice, self.bob, first, DAY)
        with self.assertRaises(services.LimitExceeded):
            services.post_transfer(self.alice, self.bob, Money(11, "EUR"), DAY)
        services.post_transfer(self.alice, self.bob, Money(10, "EUR"), DAY)
        self.assertEqual(services.sent_today(self.alice, DAY), first + Money(10, "EUR"))

    def test_limit_resets_on_the_next_day(self):
        services.post_transfer(self.alice, self.bob, self.limit, DAY)
        next_day = DAY + dt.timedelta(days=1)
        services.post_transfer(self.alice, self.bob, Money(100, "EUR"), next_day)
        self.assertEqual(services.sent_today(self.alice, next_day), Money(100, "EUR"))

    def test_review_threshold_holds_the_transfer(self):
        rich = self.make_account("Rich", "100200300400500600", balance=50_000_000, risk_class=3,
                                 opened_on=dt.date(2020, 1, 1), created_on=dt.date(2020, 1, 1))
        threshold = rules.aml_review_threshold_cents(3)
        with self.assertRaises(services.HeldForReview):
            services.post_transfer(rich, self.bob, Money(threshold, "EUR"), DAY)
        self.assertEqual(JournalEntry.objects.count(), 0)

    def test_high_risk_destination_country_is_held(self):
        with self.assertRaises(services.HeldForReview):
            services.post_transfer(self.alice, self.bob, Money(100, "EUR"), DAY, destination_country="IR")

    def test_insufficient_funds(self):
        poor = self.make_account("Poor", "200300400500600700", balance=1000)
        amount = Money(self.limit.minor // 2, "EUR")
        overdraft = account_services.overdraft_limit(poor, DAY)
        self.assertGreater(amount.minor + fees.wire_fee(amount).minor, 1000 + overdraft.minor)
        with self.assertRaises(services.InsufficientFunds):
            services.post_transfer(poor, self.bob, amount, DAY)
        self.refresh(poor)
        self.assertEqual(poor.balance_minor, 1000)

    def test_frozen_account_cannot_send(self):
        account_services.freeze(self.alice)
        with self.assertRaises(services.LedgerError):
            services.post_transfer(self.alice, self.bob, Money(100, "EUR"), DAY)

    def test_amount_must_be_positive_and_in_source_currency(self):
        with self.assertRaises(services.LedgerError):
            services.post_transfer(self.alice, self.bob, Money(0, "EUR"), DAY)
        with self.assertRaises(services.LedgerError):
            services.post_transfer(self.alice, self.bob, Money(100, "USD"), DAY)

    def test_cross_currency_transfer_converts_and_charges_markup(self):
        usd = self.make_account("Dollar", "300400500600700800", currency="USD")
        amount = Money(self.limit.minor // 2, "EUR")
        services.post_transfer(self.alice, usd, amount, DAY, rate_micro=1_084_500)
        self.refresh(self.alice, usd)
        self.assertEqual(usd.balance_minor, amount.convert(1_084_500, "USD").minor)
        cost = fees.transfer_cost(amount, cross_currency=True)
        self.assertEqual(self.alice.balance_minor, 10_000_000 - amount.minor - cost.minor)
        self.assertEqual(services.trial_balance("EUR"), 0)
        self.assertEqual(services.trial_balance("USD"), 0)

    def test_cross_currency_requires_a_rate(self):
        usd = self.make_account("Dollar", "300400500600700800", currency="USD")
        with self.assertRaises(services.LedgerError):
            services.post_transfer(self.alice, usd, Money(100, "EUR"), DAY)


class UnbalancedEntryTests(LedgerTestCase):
    def test_unbalanced_legs_are_refused(self):
        with self.assertRaises(services.LedgerError):
            services._book("transfer", DAY, [(self.alice, Money(-100, "EUR")), (self.bob, Money(99, "EUR"))])
        self.assertEqual(JournalEntry.objects.count(), 0)


class MonthEndTests(LedgerTestCase):
    def test_month_end_credits_interest_and_charges_fee(self):
        self.alice.balance_minor = 2_000_000
        self.alice.save(update_fields=["balance_minor"])
        start = Money(2_000_000, "EUR")
        earned, charge = services.month_end(self.alice, DAY, 31)
        self.refresh(self.alice)
        self.assertEqual(self.alice.balance_minor, start.minor + earned.minor - charge.minor)
        self.assertEqual(earned.minor > 0, True)
        self.assertEqual(services.trial_balance("EUR"), 0)


class StatementTests(LedgerTestCase):
    def test_running_balance_and_totals(self):
        for offset in range(3):
            services.post_transfer(self.alice, self.bob, Money(1000, "EUR"), DAY + dt.timedelta(days=offset))
        page = services.statement(self.bob)
        self.assertEqual(page["total"], 3)
        self.assertEqual([r["running_minor"] for r in page["rows"]], [1000, 2000, 3000])
        self.assertEqual(page["page_size"], rules.statement_page_size(3))

    def test_pagination(self):
        for offset in range(5):
            services.post_transfer(self.alice, self.bob, Money(500, "EUR"), DAY + dt.timedelta(days=offset))
        with mock.patch("ledger.services.settlement.page_size", return_value=2):
            self.assertEqual(len(services.statement(self.bob, 1)["rows"]), 2)
            self.assertEqual(len(services.statement(self.bob, 3)["rows"]), 1)
            self.assertEqual(services.statement(self.bob, 4)["rows"], [])

    def test_system_account_is_reused(self):
        a = services.system_account("EUR", DAY)
        self.assertEqual(services.system_account("EUR", DAY), a)
        self.assertNotEqual(services.system_account("USD", DAY), a)
