from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.commerce.webhook_service import PaymentWebhookService, WebhookProcessingError


@csrf_exempt
@require_POST
def cryptobot_webhook(request, secret_path: str):
    try:
        result = PaymentWebhookService.process_cryptobot(
            secret_path=secret_path,
            raw_body=request.body,
            headers=request.headers,
        )
    except WebhookProcessingError as exc:
        code = str(exc)
        if code == "not_found":
            return HttpResponse(status=404)
        if code == "invalid_signature":
            return HttpResponse(status=400)
        return HttpResponse(status=400)

    return JsonResponse({"ok": True, "result": result})
