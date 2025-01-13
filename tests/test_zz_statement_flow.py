import datetime as dt
import json

from django.test import TestCase

from accounts import services as account_services
from accounts.models import Customer
from ledger import services
from ledgerkit import fees, rules
from ledgerkit.money import Money

SENDER = "DE89370400440532013000"
RECEIVER = "DE41500105170123456789"


class StatementFlowTests(TestCase):
    """A week of payments through the HTTP API, then month-end processing and reconciliation."""

    def setUp(self):
        c1 = Customer.objects.create(name="Payer", created_on=dt.date(2024, 6, 1))
        c2 = Customer.objects.create(name="Payee", created_on=dt.date(2024, 6, 1))
        self.payer = account_services.open_account(c1, "370400440532013000", "EUR", dt.date(2024, 6, 2))
        self.payee = account_services.open_account(c2, "500105170123456789", "EUR", dt.date(2024, 6, 2))
        self.payer.balance_minor = 3_000_000
        self.payer.save(update_fields=["balance_minor"])

    def pay(self, day, amount):
        body = {"from": SENDER, "to": RECEIVER, "amount_minor": amount, "currency": "EUR", "booked_on": day.isoformat()}
        return self.client.post("/ledger/post/", json.dumps(body), content_type="application/json")

    def test_week_of_payments_reconciles(self):
        start = dt.date(2025, 3, 3)
        amounts = [1200, 4550, 9900, 150, 25000]
        for i, amount in enumerate(amounts):
            self.assertEqual(self.pay(start + dt.timedelta(days=i), amount).status_code, 201)
        rows = self.client.get(f"/ledger/{SENDER}/statement/").json()
        self.assertEqual(rows["total"], len(amounts) + sum(1 for a in amounts if rules.wire_fee_cents(a)))
        self.payer.refresh_from_db()
        self.assertEqual(rows["rows"][-1]["running_minor"], self.payer.balance_minor - 3_000_000)
        spent = sum(amounts) + sum(rules.wire_fee_cents(a) for a in amounts)
        self.assertEqual(self.payer.balance_minor, 3_000_000 - spent)
        self.assertEqual(self.client.get("/ledger/trial/EUR/").json()["sum_minor"], 0)

    def test_month_end_after_payments(self):
        self.pay(dt.date(2025, 3, 3), 10_000)
        self.payer.refresh_from_db()
        before = Money(self.payer.balance_minor, "EUR")
        earned, charge = services.month_end(self.payer, dt.date(2025, 3, 31), 31)
        self.payer.refresh_from_db()
        self.assertEqual(self.payer.balance_minor, (before + earned - charge).minor)
        self.assertEqual(charge, fees.monthly_account_fee(before))
        self.assertEqual(services.trial_balance("EUR"), 0)
