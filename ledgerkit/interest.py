"""Interest accrual on balances."""
from . import native, rules
from .money import Money

DAYS_PER_YEAR = 365


def annual_rate_bp(balance):
    return rules.interest_rate_bp(max(balance.minor, 0))


def daily_interest(balance, days=1):
    """Interest for `days` days; banker's rounding, never negative for an overdrawn balance."""
    if balance.minor <= 0:
        return Money.zero(balance.currency)
    yearly = balance.percent_bp(annual_rate_bp(balance), native.ROUND_DOWN)
    scaled = native.mul_checked(yearly.minor, days)
    return Money(native.round_div(scaled, DAYS_PER_YEAR, native.ROUND_HALF_EVEN), balance.currency)


def accrue(balance, days_in_period):
    """New balance after crediting interest for the period."""
    return balance + daily_interest(balance, days_in_period)


def dormancy_charge_due(balance, idle_days):
    """True when an idle account has crossed the dormancy limit for its balance."""
    return idle_days > rules.dormancy_days(max(balance.minor, 0))
