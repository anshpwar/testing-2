from django.http import Http404, JsonResponse

from .models import Transfer


def summary(request, ref):
    try:
        obj = Transfer.objects.get(ref=ref)
    except Transfer.DoesNotExist:
        raise Http404
    return JsonResponse({"ref": obj.ref, "amount_cents": obj.amount_cents, "status": obj.status})
