import unittest

from ledgerkit import contract, consumer_83


class ExportTests(unittest.TestCase):
    def test_export_line(self):
        rec = contract.Record("LG-9", 700, "open")
        self.assertEqual(consumer_83.export_line(rec), "LG-9,700")
