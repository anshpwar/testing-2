import unittest

from ledgerkit import contract, consumer_82


class ExportTests(unittest.TestCase):
    def test_export_line(self):
        rec = contract.Record("LG-9", 700, "open")
        self.assertEqual(consumer_82.export_line(rec), "LG-9,700")
