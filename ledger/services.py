"""Double-entry posting. Money arithmetic runs in the C library; limits and fees come from the policy tables."""
from django.db import transaction
from django.db.models import Sum

from accounts import services as account_services
from accounts.models import Account, Customer
from ledgerkit import fees, iban as ibanlib, interest, screening, settlement
from ledgerkit.money import Money

from .models import JournalEntry, Posting

CURRENCY_CODES = {"EUR": 978, "USD": 840, "GBP": 826, "CHF": 756, "SEK": 752, "PLN": 985, "JPY": 392, "KWD": 414}


class LedgerError(Exception):
    pass


class HeldForReview(LedgerError):
    pass


class LimitExceeded(LedgerError):
    pass


class InsufficientFunds(LedgerError):
    pass


def system_account(currency, today):
    """The bank's own account for a currency; fees, conversion legs and interest are booked against it."""
    code = CURRENCY_CODES[currency]
    iban = ibanlib.generate("DE", f"99990000{code:03d}0000000")
    try:
        return Account.objects.get(iban=iban)
    except Account.DoesNotExist:
        owner, _ = Customer.objects.get_or_create(name="Ledger Operations", defaults={"created_on": today})
        return Account.objects.create(customer=owner, iban=iban, currency=currency, opened_on=today)


def _next_ref():
    return f"LG-{JournalEntry.objects.count() + 1:07d}"


@transaction.atomic
def _book(kind, booked_on, legs, memo=""):
    """Write one balanced entry. `legs` is a list of (account, Money); every currency must net to zero."""
    totals = {}
    for _account, money in legs:
        totals[money.currency] = totals.get(money.currency, 0) + money.minor
    if any(total != 0 for total in totals.values()):
        raise LedgerError("entry does not balance")
    entry = JournalEntry.objects.create(ref=_next_ref(), booked_on=booked_on, kind=kind, memo=memo)
    for account, money in legs:
        account.refresh_from_db()
        updated = Money(account.balance_minor, account.currency) + money
        account.balance_minor = updated.minor
        account.last_activity_on = booked_on
        account.save(update_fields=["balance_minor", "last_activity_on"])
        Posting.objects.create(entry=entry, account=account, amount_minor=money.minor, currency=money.currency)
    return entry


def sent_today(account, booked_on):
    total = Posting.objects.filter(account=account, entry__booked_on=booked_on, entry__kind="transfer",
                                   amount_minor__lt=0).aggregate(total=Sum("amount_minor"))["total"]
    return Money(-(total or 0), account.currency)


def post_transfer(src, dst, amount, booked_on, memo="", rate_micro=None, destination_country=None):
    """Move `amount` (in the source currency) from src to dst, charging the sender's fees in a separate entry."""
    if src.status != Account.ACTIVE or dst.status != Account.ACTIVE:
        raise LedgerError("both accounts must be active")
    if amount.minor <= 0 or amount.currency != src.currency:
        raise LedgerError("amount must be positive and in the source currency")
    cross = src.currency != dst.currency
    if cross and not rate_micro:
        raise LedgerError("a conversion rate is required between different currencies")

    decision = screening.screen(amount, src.customer.risk_class, destination_country)
    if decision.review:
        raise HeldForReview(decision.reason)

    if sent_today(src, booked_on) + amount > account_services.daily_limit(src, booked_on):
        raise LimitExceeded("daily transfer limit reached")

    cost = fees.transfer_cost(amount, cross_currency=cross)
    projected = account_services.balance(src) - amount - cost
    if projected < -account_services.overdraft_limit(src, booked_on):
        raise InsufficientFunds("overdraft limit would be exceeded")

    bank_src = system_account(src.currency, booked_on)
    legs = [(src, -amount), (bank_src if cross else dst, amount)]
    if cross:
        converted = amount.convert(rate_micro, dst.currency)
        bank_dst = system_account(dst.currency, booked_on)
        legs += [(bank_dst, -converted), (dst, converted)]
    with transaction.atomic():
        entry = _book("transfer", booked_on, legs, memo)
        if cost.minor:
            _book("fee", booked_on, [(src, -cost), (bank_src, cost)], f"fees for {entry.ref}")
    return entry


def balance_from_postings(account):
    total = account.postings.aggregate(total=Sum("amount_minor"))["total"] or 0
    return Money(total, account.currency)


def trial_balance(currency):
    """Sum of every posting in a currency; zero when the books balance."""
    return Posting.objects.filter(currency=currency).aggregate(total=Sum("amount_minor"))["total"] or 0


def month_end(account, booked_on, days_in_period):
    """Credit interest and charge the maintenance fee for the period; returns (interest, fee)."""
    bank = system_account(account.currency, booked_on)
    earned = interest.daily_interest(account_services.balance(account), days_in_period)
    charge = fees.monthly_account_fee(account_services.balance(account))
    if earned.minor:
        _book("interest", booked_on, [(bank, -earned), (account, earned)], "interest credit")
    if charge.minor:
        _book("fee", booked_on, [(account, -charge), (bank, charge)], "monthly maintenance")
    return earned, charge


def statement(account, page=1):
    """One page of postings with a running balance; the page size follows the account's activity."""
    postings = list(account.postings.select_related("entry"))
    size = settlement.page_size(len(postings))
    running = 0
    rows = []
    for p in postings:
        running += p.amount_minor
        rows.append({"ref": p.entry.ref, "booked_on": p.entry.booked_on.isoformat(), "kind": p.entry.kind,
                     "amount_minor": p.amount_minor, "running_minor": running})
    start = (max(page, 1) - 1) * size
    return {"page": max(page, 1), "page_size": size, "total": len(rows), "rows": rows[start:start + size]}
