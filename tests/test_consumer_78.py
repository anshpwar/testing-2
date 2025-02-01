import unittest

from ledgerkit import consumer_78


class SettlementFeeTests(unittest.TestCase):
    def test_proportional_fee(self):
        self.assertEqual(consumer_78.proportional_fee(10000, 250), 250)
        self.assertEqual(consumer_78.proportional_fee(4000, 125), 50)

    def test_fee_column(self):
        self.assertEqual(consumer_78.fee_column([(10000, 100), (2000, 50)]), [100, 10])
