import datetime as dt
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from accounts import services as account_services
from ledgerkit.money import CurrencyError, Money
from ledgerkit.native import NativeError

from . import services

ERROR_STATUS = {
    services.HeldForReview: (422, "held_for_review"),
    services.LimitExceeded: (422, "limit_exceeded"),
    services.InsufficientFunds: (409, "insufficient_funds"),
}


@csrf_exempt
@require_POST
def post(request):
    try:
        body = json.loads(request.body or b"{}")
        src = account_services.lookup(body["from"])
        dst = account_services.lookup(body["to"])
        amount = Money(int(body["amount_minor"]), str(body["currency"]))
        booked_on = dt.date.fromisoformat(body["booked_on"])
    except (json.JSONDecodeError, KeyError, ValueError, TypeError, CurrencyError):
        return JsonResponse({"error": "bad_request"}, status=400)
    except account_services.AccountError as exc:
        return JsonResponse({"error": "unknown_account", "detail": str(exc)}, status=404)
    try:
        entry = services.post_transfer(src, dst, amount, booked_on, str(body.get("memo", ""))[:80],
                                       rate_micro=body.get("rate_micro"),
                                       destination_country=body.get("country"))
    except tuple(ERROR_STATUS) as exc:
        status, code = ERROR_STATUS[type(exc)]
        return JsonResponse({"error": code, "detail": str(exc)}, status=status)
    except (services.LedgerError, NativeError) as exc:
        return JsonResponse({"error": "rejected", "detail": str(exc)}, status=400)
    return JsonResponse({"ref": entry.ref, "booked_on": entry.booked_on.isoformat()}, status=201)


@require_GET
def statement(request, iban):
    try:
        account = account_services.lookup(iban)
        page = int(request.GET.get("page", "1"))
    except account_services.AccountError as exc:
        return JsonResponse({"error": str(exc)}, status=404)
    except ValueError:
        return JsonResponse({"error": "bad_request"}, status=400)
    return JsonResponse(services.statement(account, page))


@require_GET
def trial(request, currency):
    return JsonResponse({"currency": currency, "sum_minor": services.trial_balance(currency)})
