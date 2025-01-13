"""Account lifecycle: opening, ageing, limits and login lockouts. Policy numbers come from ledgerkit."""
from ledgerkit import iban as ibanlib
from ledgerkit import interest, screening, settlement
from ledgerkit.money import Money

from .models import Account, Customer


class AccountError(Exception):
    pass


def open_account(customer, bban, currency, opened_on, country=None):
    """Open an account whose IBAN is generated from the basic account number."""
    iban = ibanlib.generate(country or customer.country, bban)
    if Account.objects.filter(iban=iban).exists():
        raise AccountError("IBAN already in use")
    return Account.objects.create(customer=customer, iban=iban, currency=currency, opened_on=opened_on)


def age_days(account, today):
    return max((today - account.opened_on).days, 0)


def tenure_months(customer, today):
    return max((today - customer.created_on).days // 30, 0)


def balance(account):
    return Money(account.balance_minor, account.currency)


def daily_limit(account, today):
    return settlement.daily_limit(age_days(account, today), account.currency)


def instant_cap(account, today):
    return settlement.instant_cap(age_days(account, today), account.currency)


def overdraft_limit(account, today):
    return settlement.overdraft_limit(tenure_months(account.customer, today), account.currency)


def is_dormant(account, today):
    last = account.last_activity_on or account.opened_on
    return interest.dormancy_charge_due(balance(account), (today - last).days)


def register_failed_login(customer):
    """Count a failed login and return the lockout in seconds (0 means not locked)."""
    customer.failed_logins += 1
    customer.save(update_fields=["failed_logins"])
    return screening.login_lockout_seconds(customer.failed_logins)


def freeze(account):
    account.status = Account.FROZEN
    account.save(update_fields=["status"])
    return account


def lookup(iban_text):
    try:
        return Account.objects.get(iban=ibanlib.validate(iban_text))
    except ibanlib.IbanError as exc:
        raise AccountError(str(exc)) from exc
    except Account.DoesNotExist:
        raise AccountError("unknown account") from None


def customers_in_class(risk_class):
    return Customer.objects.filter(risk_class=risk_class)
