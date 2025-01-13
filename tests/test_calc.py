import unittest

from ledgerkit import calc


class CalcTests(unittest.TestCase):
    def test_combined_charge(self):
        self.assertEqual(calc.combined_charge(0), 650)
        self.assertEqual(calc.combined_charge(1), 650)
        self.assertEqual(calc.combined_charge(100000), 650)
        self.assertEqual(calc.combined_charge(100001), 1600)
