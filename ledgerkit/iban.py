"""IBAN helpers: normalisation, validation and generation on top of the C mod-97 routine."""
from . import native


class IbanError(ValueError):
    def __init__(self, message, code):
        super().__init__(message)
        self.code = code


def normalise(text):
    """Strip separators and upper-case, as users paste IBANs in groups of four."""
    return "".join(text.split()).replace("-", "").upper()


def validate(text):
    """Return the normalised IBAN or raise IbanError."""
    iban = normalise(text)
    status = native.iban_status(iban)
    if status != native.OK:
        raise IbanError(native.ERROR_NAMES.get(status, "invalid IBAN"), status)
    return iban


def is_valid(text):
    try:
        validate(text)
    except IbanError:
        return False
    return True


def generate(country, bban):
    """Build a valid IBAN from a country code and a basic bank account number."""
    country = country.upper()
    bban = normalise(bban)
    expected = native.iban_expected_length(country)
    if len(bban) + 4 != expected:
        raise IbanError("wrong BBAN length", native.ERR_IBAN_LENGTH)
    return validate(country + native.iban_check_digits(country, bban) + bban)


def group(iban):
    """Print form: groups of four separated by spaces."""
    iban = normalise(iban)
    return " ".join(iban[i:i + 4] for i in range(0, len(iban), 4))


def country_of(iban):
    return native.iban_parse(validate(iban))["country"]
