import unittest

from ledgerkit import iban, native

SAMPLES = [
    "DE89370400440532013000",
    "GB82WEST12345698765432",
    "FR1420041010050500013M02606",
    "ES9121000418450200051332",
    "NL91ABNA0417164300",
    "CH9300762011623852957",
    "BE68539007547034",
    "IT60X0542811101000000123456",
    "AT611904300234573201",
    "PL61109010140000071219812874",
]


class IbanTests(unittest.TestCase):
    def test_known_samples_validate(self):
        for sample in SAMPLES:
            self.assertEqual(iban.validate(sample), sample)

    def test_normalise_handles_print_form(self):
        self.assertEqual(iban.normalise("de89 3704-0044 0532 0130 00"), "DE89370400440532013000")
        self.assertEqual(iban.validate("gb82 west 1234 5698 7654 32"), "GB82WEST12345698765432")

    def test_group_is_four_character_blocks(self):
        self.assertEqual(iban.group("NL91ABNA0417164300"), "NL91 ABNA 0417 1643 00")

    def test_failure_codes(self):
        cases = {
            "DE88370400440532013000": native.ERR_IBAN_CHECK,
            "DE8937040044053201300": native.ERR_IBAN_LENGTH,
            "ZZ89370400440532013000": native.ERR_IBAN_COUNTRY,
            "DE": native.ERR_IBAN_LENGTH,
        }
        for text, code in cases.items():
            with self.assertRaises(iban.IbanError) as ctx:
                iban.validate(text)
            self.assertEqual(ctx.exception.code, code, text)

    def test_single_digit_error_is_always_detected(self):
        base = "DE89370400440532013000"
        for i in range(4, len(base)):
            changed = base[:i] + str((int(base[i]) + 1) % 10) + base[i + 1:]
            self.assertFalse(iban.is_valid(changed), changed)

    def test_adjacent_transposition_is_detected(self):
        self.assertFalse(iban.is_valid("DE89370400440532013000".replace("4004", "4040")))

    def test_generate_matches_published_samples(self):
        self.assertEqual(iban.generate("DE", "370400440532013000"), "DE89370400440532013000")
        self.assertEqual(iban.generate("gb", "WEST12345698765432"), "GB82WEST12345698765432")
        self.assertEqual(iban.generate("NL", "ABNA0417164300"), "NL91ABNA0417164300")

    def test_generate_rejects_wrong_length(self):
        with self.assertRaises(iban.IbanError):
            iban.generate("DE", "12345")

    def test_generated_ibans_always_validate(self):
        for n in range(0, 500, 37):
            bban = f"{10000000 + n:08d}{n:010d}"
            self.assertTrue(iban.is_valid(iban.generate("DE", bban)))

    def test_country_of(self):
        self.assertEqual(iban.country_of("FR1420041010050500013M02606"), "FR")
