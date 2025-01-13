import datetime as dt
import json

from django.test import TestCase

from accounts import services as account_services
from accounts.models import Customer
from ledgerkit import fees, rules
from ledgerkit.money import Money

DAY = "2025-03-01"
SENDER = "DE89370400440532013000"
RECEIVER = "DE41500105170123456789"


class LedgerApiTests(TestCase):
    def setUp(self):
        c1 = Customer.objects.create(name="Sender", created_on=dt.date(2025, 2, 1))
        c2 = Customer.objects.create(name="Receiver", created_on=dt.date(2025, 2, 1))
        self.sender = account_services.open_account(c1, "370400440532013000", "EUR", dt.date(2025, 2, 24))
        self.receiver = account_services.open_account(c2, "500105170123456789", "EUR", dt.date(2025, 2, 24))
        self.sender.balance_minor = 5_000_000
        self.sender.save(update_fields=["balance_minor"])
        self.limit = account_services.daily_limit(self.sender, dt.date.fromisoformat(DAY)).minor

    def post(self, body):
        return self.client.post("/ledger/post/", json.dumps(body), content_type="application/json")

    def payload(self, amount, **extra):
        return {"from": SENDER, "to": RECEIVER, "amount_minor": amount, "currency": "EUR", "booked_on": DAY, **extra}

    def test_post_transfer_round_trip(self):
        amount = self.limit // 2
        resp = self.post(self.payload(amount, memo="invoice 17"))
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["ref"], "LG-0000001")
        detail = self.client.get(f"/accounts/{SENDER}/").json()
        self.assertEqual(detail["balance_minor"], 5_000_000 - amount - rules.wire_fee_cents(amount))
        self.assertEqual(self.client.get(f"/accounts/{RECEIVER}/").json()["balance_minor"], amount)

    def test_error_mapping(self):
        self.assertEqual(self.post({"from": SENDER}).status_code, 400)
        self.assertEqual(self.post(self.payload(100, to="DE88370400440532013000")).status_code, 404)
        self.assertEqual(self.post(self.payload(100, currency="XXX")).status_code, 400)
        self.assertEqual(self.post(self.payload(0)).status_code, 400)
        over = self.post(self.payload(self.limit + 1))
        self.assertEqual((over.status_code, over.json()["error"]), (422, "limit_exceeded"))
        held = self.post(self.payload(100, country="KP"))
        self.assertEqual((held.status_code, held.json()["error"]), (422, "held_for_review"))

    def test_insufficient_funds_is_a_conflict(self):
        self.sender.balance_minor = 10
        self.sender.save(update_fields=["balance_minor"])
        resp = self.post(self.payload(self.limit // 2))
        self.assertEqual((resp.status_code, resp.json()["error"]), (409, "insufficient_funds"))

    def test_statement_endpoint(self):
        self.post(self.payload(1000))
        page = self.client.get(f"/ledger/{RECEIVER}/statement/").json()
        self.assertEqual(page["total"], 1)
        self.assertEqual(page["rows"][0]["running_minor"], 1000)
        self.assertEqual(self.client.get(f"/ledger/{RECEIVER}/statement/?page=x").status_code, 400)

    def test_trial_balance_endpoint(self):
        self.post(self.payload(2500))
        self.assertEqual(self.client.get("/ledger/trial/EUR/").json(), {"currency": "EUR", "sum_minor": 0})
