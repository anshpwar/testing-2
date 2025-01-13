"""Composite charges built from the policy tables."""
from . import rules


def combined_charge(x):
    """Total of the two base schedules for x."""
    return rules.wire_fee_cents(x) + rules.fx_markup_bp(x)
