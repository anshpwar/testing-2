import json

from django.test import TestCase

from transfers.models import Transfer


class TransferApiTests(TestCase):
    def test_summary_endpoint(self):
        Transfer.objects.create(ref="LG-200", amount_cents=1999, status="paid")
        resp = self.client.get("/entries/LG-200/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content), {"ref": "LG-200", "amount_cents": 1999, "status": "paid"})

    def test_unknown_ref_is_404(self):
        self.assertEqual(self.client.get("/entries/nope/").status_code, 404)
