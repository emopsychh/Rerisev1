from celery import shared_task
from django.utils.dateparse import parse_datetime

from apps.admin_ops.services import AuditLogger
from apps.commerce.models import Payment
from apps.commerce.services import PaymentConfirmationService
from apps.commerce.webhook_service import PaymentSyncService


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def fulfill_order(self, payment_id: int, paid_at_iso: str | None = None):
    try:
        payment = Payment.objects.select_related("order").get(pk=payment_id)
    except Payment.DoesNotExist:
        return {"ok": False, "reason": "payment_not_found"}

    paid_at = parse_datetime(paid_at_iso) if paid_at_iso else None
    order = PaymentConfirmationService.confirm(payment, paid_at=paid_at)
    AuditLogger.record(
        actor=None,
        action="order_fulfilled",
        target_type="order",
        target_id=order.pk,
        new_value={"payment_id": payment_id, "status": order.status},
    )
    return {"ok": True, "order_id": order.pk, "status": order.status}


@shared_task
def sync_pending_payments():
    return PaymentSyncService.sync_pending()
