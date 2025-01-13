"""Money value type backed by the C fixed-point library."""
from dataclasses import dataclass

from . import native

CURRENCY_EXPONENTS = {"USD": 2, "EUR": 2, "GBP": 2, "CHF": 2, "SEK": 2, "PLN": 2, "JPY": 0, "KWD": 3}


class CurrencyError(ValueError):
    pass


def exponent_for(currency):
    try:
        return CURRENCY_EXPONENTS[currency]
    except KeyError:
        raise CurrencyError(f"unsupported currency {currency!r}") from None


@dataclass(frozen=True)
class Money:
    minor: int
    currency: str

    def __post_init__(self):
        exponent_for(self.currency)

    @property
    def exponent(self):
        return exponent_for(self.currency)

    def _t(self):
        return (self.minor, self.exponent, self.currency)

    @classmethod
    def _from(cls, t):
        return cls(t[0], t[2])

    @classmethod
    def zero(cls, currency):
        return cls(0, currency)

    @classmethod
    def parse(cls, text, currency):
        """Parse a decimal string such as '12.34' into minor units, rejecting extra precision."""
        exp = exponent_for(currency)
        sign = -1 if text.startswith("-") else 1
        whole, _, frac = text.lstrip("-").partition(".")
        if not whole.isdigit() or (frac and not frac.isdigit()) or len(frac) > exp:
            raise ValueError(f"bad amount {text!r} for {currency}")
        frac_part = int(frac.ljust(exp, "0")) if exp else 0
        return cls(sign * (int(whole) * 10 ** exp + frac_part), currency)

    def __add__(self, other):
        return self._from(native.money_add(self._t(), other._t()))

    def __sub__(self, other):
        return self._from(native.money_sub(self._t(), other._t()))

    def __neg__(self):
        return self._from(native.money_mul_int(self._t(), -1))

    def __mul__(self, k):
        return self._from(native.money_mul_int(self._t(), k))

    __rmul__ = __mul__

    def __lt__(self, other):
        return native.money_cmp(self._t(), other._t()) < 0

    def __le__(self, other):
        return native.money_cmp(self._t(), other._t()) <= 0

    def __gt__(self, other):
        return native.money_cmp(self._t(), other._t()) > 0

    def __ge__(self, other):
        return native.money_cmp(self._t(), other._t()) >= 0

    def is_negative(self):
        return self.minor < 0

    def percent_bp(self, bp, mode=native.ROUND_HALF_UP):
        return self._from(native.money_percent_bp(self._t(), bp, mode))

    def convert(self, rate_micro, to_currency, mode=native.ROUND_HALF_EVEN):
        return self._from(native.money_convert(self._t(), rate_micro, to_currency, exponent_for(to_currency), mode))

    def allocate(self, ratios):
        """Split into parts proportional to integer ratios; the parts always sum back to the original."""
        total = sum(ratios)
        if total <= 0 or any(r < 0 for r in ratios):
            raise ValueError("ratios must be non-negative with a positive sum")
        parts = [native.round_div(self.minor * r, total, native.ROUND_DOWN) for r in ratios]
        step = 1 if self.minor >= 0 else -1
        left = self.minor - sum(parts)
        i = 0
        while left != 0:
            if ratios[i % len(ratios)] > 0:
                parts[i % len(ratios)] += step
                left -= step
            i += 1
        return [Money(p, self.currency) for p in parts]

    def format(self):
        exp = self.exponent
        sign = "-" if self.minor < 0 else ""
        digits = str(abs(self.minor)).rjust(exp + 1, "0")
        whole, frac = (digits[:-exp], digits[-exp:]) if exp else (digits, "")
        text = f"{int(whole):,}" + (f".{frac}" if frac else "")
        return f"{sign}{text} {self.currency}"
