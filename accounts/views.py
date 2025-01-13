import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from ledgerkit import iban as ibanlib

from . import services


@require_GET
def detail(request, iban):
    try:
        account = services.lookup(iban)
    except services.AccountError as exc:
        return JsonResponse({"error": str(exc)}, status=404)
    return JsonResponse({
        "iban": account.iban,
        "currency": account.currency,
        "balance_minor": account.balance_minor,
        "status": account.status,
    })


@csrf_exempt
@require_POST
def validate_iban(request):
    try:
        body = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "bad_request"}, status=400)
    text = str(body.get("iban", ""))
    valid = ibanlib.is_valid(text)
    payload = {"valid": valid, "normalised": ibanlib.normalise(text)}
    if valid:
        payload["country"] = ibanlib.country_of(text)
    return JsonResponse(payload)
