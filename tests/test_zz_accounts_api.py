import datetime as dt
import json

from django.test import TestCase

from accounts import services
from accounts.models import Customer


class AccountApiTests(TestCase):
    def setUp(self):
        customer = Customer.objects.create(name="Api Customer", created_on=dt.date(2025, 1, 2))
        self.account = services.open_account(customer, "370400440532013000", "EUR", dt.date(2025, 1, 3))

    def post(self, url, body):
        return self.client.post(url, json.dumps(body), content_type="application/json")

    def test_account_detail(self):
        resp = self.client.get("/accounts/DE89370400440532013000/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"iban": "DE89370400440532013000", "currency": "EUR", "balance_minor": 0, "status": "active"})

    def test_detail_accepts_grouped_iban_and_rejects_bad_ones(self):
        self.assertEqual(self.client.get("/accounts/DE89%203704%200044%200532%200130%2000/").status_code, 200)
        self.assertEqual(self.client.get("/accounts/DE88370400440532013000/").status_code, 404)
        self.assertEqual(self.client.get("/accounts/NL91ABNA0417164300/").status_code, 404)

    def test_validate_endpoint(self):
        ok = self.post("/accounts/validate/", {"iban": "gb82 west 1234 5698 7654 32"}).json()
        self.assertEqual(ok, {"valid": True, "normalised": "GB82WEST12345698765432", "country": "GB"})
        bad = self.post("/accounts/validate/", {"iban": "GB82WEST12345698765433"}).json()
        self.assertEqual(bad, {"valid": False, "normalised": "GB82WEST12345698765433"})

    def test_validate_rejects_malformed_json(self):
        resp = self.client.post("/accounts/validate/", "{nope", content_type="application/json")
        self.assertEqual(resp.status_code, 400)

    def test_validate_requires_post(self):
        self.assertEqual(self.client.get("/accounts/validate/").status_code, 405)
