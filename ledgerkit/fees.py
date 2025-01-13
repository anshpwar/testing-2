"""Customer-facing fees. Flat schedules come from the policy tables; proportional parts use the C fee routine."""
from . import native, rules
from .money import Money


def wire_fee(amount):
    """Flat outgoing wire fee for the amount, in the amount's currency."""
    return Money(rules.wire_fee_cents(abs(amount.minor)), amount.currency)


def fx_markup(amount):
    """Margin charged on a currency conversion, proportional to the converted amount."""
    bp = rules.fx_markup_bp(abs(amount.minor))
    return Money(native.fee_minor(abs(amount.minor), bp), amount.currency)


def transfer_cost(amount, cross_currency=False):
    """Everything the sender pays on top of the amount."""
    cost = wire_fee(amount)
    if cross_currency:
        cost = cost + fx_markup(amount)
    return cost


def monthly_account_fee(balance):
    """Maintenance fee charged at month end, falling as the average balance rises."""
    return Money(rules.monthly_account_fee_cents(max(balance.minor, 0)), balance.currency)


def loan_origination_fee(principal):
    bp = rules.loan_origination_fee_bp(principal.minor)
    return Money(native.fee_minor(principal.minor, bp), principal.currency)


def round_for_display(amount):
    """Round a marketing figure to the configured step (half up, step from the policy table)."""
    step = rules.rounding_step_cents(abs(amount.minor))
    return Money(native.round_div(amount.minor, step, native.ROUND_HALF_UP) * step, amount.currency)
