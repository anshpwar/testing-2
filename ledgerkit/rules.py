"""Ledgerhub policy tables: schedules, thresholds and limits."""

def wire_fee_cents(amount_cents):
    """Flat outgoing wire fee in cents by transfer amount in cents."""
    if amount_cents <= 100000:
        return 500
    if amount_cents <= 1000000:
        return 1500
    if amount_cents <= 10000000:
        return 3500
    return 7500


def fx_markup_bp(amount_cents):
    """Currency conversion margin in basis points by converted amount in cents."""
    if amount_cents <= 100000:
        return 150
    if amount_cents <= 1000000:
        return 100
    if amount_cents <= 10000000:
        return 60
    return 35


def daily_transfer_limit_cents(age_days):
    """Maximum value in cents an account may send per day, by account age in days."""
    if age_days <= 30:
        return 50000
    if age_days <= 180:
        return 250000
    if age_days <= 365:
        return 1000000
    return 5000000


def overdraft_limit_cents(tenure_months):
    """Overdraft facility in cents by customer tenure in months."""
    if tenure_months <= 6:
        return 0
    if tenure_months <= 24:
        return 50000
    if tenure_months <= 60:
        return 200000
    return 500000


def interest_rate_bp(balance_cents):
    """Annual deposit interest in basis points by balance in cents."""
    if balance_cents <= 100000:
        return 10
    if balance_cents <= 1000000:
        return 25
    if balance_cents <= 10000000:
        return 45
    return 60


def monthly_account_fee_cents(balance_cents):
    """Monthly maintenance fee in cents by average balance in cents."""
    if balance_cents <= 50000:
        return 1200
    if balance_cents <= 500000:
        return 500
    if balance_cents <= 2500000:
        return 200
    return 0


def aml_review_threshold_cents(risk_class):
    """Transfer value in cents that triggers manual review, by customer risk class."""
    if risk_class <= 1:
        return 1000000
    if risk_class <= 2:
        return 500000
    if risk_class <= 3:
        return 200000
    return 100000


def settlement_delay_hours(amount_cents):
    """Hours before a transfer settles, by amount in cents."""
    if amount_cents <= 100000:
        return 1
    if amount_cents <= 1000000:
        return 4
    if amount_cents <= 10000000:
        return 24
    return 72


def chargeback_window_days(amount_cents):
    """Days in which a transfer may be disputed, by amount in cents."""
    if amount_cents <= 10000:
        return 60
    if amount_cents <= 100000:
        return 90
    if amount_cents <= 1000000:
        return 120
    return 180


def reserve_ratio_bp(deposit_cents):
    """Liquidity reserve in basis points held against a deposit total in cents."""
    if deposit_cents <= 1000000:
        return 100
    if deposit_cents <= 10000000:
        return 200
    if deposit_cents <= 100000000:
        return 400
    return 1000


def rounding_step_cents(amount_cents):
    """Step in cents to which marketing figures are rounded."""
    if amount_cents <= 9999:
        return 1
    if amount_cents <= 99999:
        return 5
    if amount_cents <= 999999:
        return 25
    return 100


def failed_login_lockout_s(attempts):
    """Seconds a customer is locked out, by number of consecutive failed logins."""
    if attempts <= 3:
        return 0
    if attempts <= 5:
        return 60
    if attempts <= 8:
        return 900
    return 86400


def dormancy_days(balance_cents):
    """Idle days after which an account counts as dormant, by balance in cents."""
    if balance_cents <= 10000:
        return 180
    if balance_cents <= 1000000:
        return 365
    if balance_cents <= 10000000:
        return 730
    return 1095


def statement_page_size(postings):
    """Rows per statement page by number of postings on the account."""
    if postings <= 50:
        return 25
    if postings <= 500:
        return 100
    if postings <= 5000:
        return 250
    return 500


def loan_origination_fee_bp(principal_cents):
    """Loan origination fee in basis points by principal in cents."""
    for bound, value in ((1000000, 165), (10000000, 110), (50000000, 82),):
        if principal_cents <= bound:
            return value
    return 55


def instant_payment_cap_cents(age_days):
    """Cap in cents for an instant payment, by account age in days."""
    if age_days <= 30:
        return 100000
    if age_days <= 180:
        return 500000
    if age_days <= 365:
        return 1500000
    return 10000000
