from django.test import TestCase

from transfers.models import Transfer


class TransferModelTests(TestCase):
    def test_defaults(self):
        obj = Transfer.objects.create(ref="LG-100", amount_cents=500)
        self.assertEqual(obj.status, "open")
        self.assertEqual(str(obj), "LG-100")

    def test_ref_is_unique(self):
        Transfer.objects.create(ref="LG-101", amount_cents=1)
        with self.assertRaises(Exception):
            Transfer.objects.create(ref="LG-101", amount_cents=2)
