"""Transaction screening: decides which transfers need manual review before posting."""
from dataclasses import dataclass

from . import rules
from .money import Money

HIGH_RISK_COUNTRIES = frozenset({"KP", "IR", "SY"})


@dataclass(frozen=True)
class Decision:
    review: bool
    reason: str


def review_threshold(risk_class):
    return Money(rules.aml_review_threshold_cents(risk_class), "EUR")


def screen(amount, risk_class, destination_country=None):
    """Return a Decision for an outgoing transfer. Amounts are compared in the threshold currency's minor units."""
    if destination_country in HIGH_RISK_COUNTRIES:
        return Decision(True, "destination country is on the high-risk list")
    limit = rules.aml_review_threshold_cents(risk_class)
    if abs(amount.minor) >= limit:
        return Decision(True, f"amount reaches the class {risk_class} review threshold")
    return Decision(False, "clear")


def login_lockout_seconds(failed_attempts):
    return rules.failed_login_lockout_s(failed_attempts)
