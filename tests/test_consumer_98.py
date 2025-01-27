import ctypes
import unittest

from ledgerkit import consumer_98, native


class StatementRowTests(unittest.TestCase):
    def test_row_layout_matches_the_library(self):
        self.assertEqual(ctypes.sizeof(consumer_98.LkMoneyV1), native.money_sizeof())

    def test_pack_unpack_round_trip(self):
        raw = consumer_98.pack_row(-1250, 2, "EUR")
        self.assertEqual(len(raw), consumer_98.ROW_SIZE)
        self.assertEqual(consumer_98.unpack_row(raw), (-1250, 2, "EUR"))

    def test_unpack_rejects_wrong_size(self):
        with self.assertRaises(ValueError):
            consumer_98.unpack_row(b"short")
