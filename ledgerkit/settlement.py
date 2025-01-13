"""Settlement timing and customer limits derived from account age and amount."""
import datetime as dt

from . import rules
from .money import Money


def settlement_hours(amount):
    return rules.settlement_delay_hours(abs(amount.minor))


def settles_at(booked_at, amount):
    """Datetime at which a transfer booked at `booked_at` is final."""
    return booked_at + dt.timedelta(hours=settlement_hours(amount))


def chargeback_deadline(booked_on, amount):
    return booked_on + dt.timedelta(days=rules.chargeback_window_days(abs(amount.minor)))


def daily_limit(age_days, currency="EUR"):
    return Money(rules.daily_transfer_limit_cents(age_days), currency)


def instant_cap(age_days, currency="EUR"):
    return Money(rules.instant_payment_cap_cents(age_days), currency)


def overdraft_limit(tenure_months, currency="EUR"):
    return Money(rules.overdraft_limit_cents(tenure_months), currency)


def reserve_required(deposits):
    """Liquidity reserve the bank must hold against a deposit total."""
    return deposits.percent_bp(rules.reserve_ratio_bp(max(deposits.minor, 0)))


def page_size(entry_count):
    return rules.statement_page_size(entry_count)
