from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.admin_ops.services import AuditLogger
from apps.commerce.models import Order, Payment
from apps.commerce.providers.base import (
    IgnoredWebhookError,
    InvalidSignatureError,
    PaymentEvent,
)
from apps.commerce.providers.cryptobot import CryptoBotProvider
from apps.commerce.providers.registry import get_payment_provider
from apps.commerce.replay import mark_webhook_seen


class WebhookProcessingError(ValueError):
    pass


class PaymentWebhookService:
    @staticmethod
    def process_cryptobot(
        *,
        secret_path: str,
        raw_body: bytes,
        headers,
    ) -> str:
        expected = settings.CRYPTOBOT_WEBHOOK_SECRET_PATH
        if not expected or secret_path != expected:
            raise WebhookProcessingError("not_found")

        provider = CryptoBotProvider()
        try:
            event = provider.verify_webhook(raw_body, headers)
        except InvalidSignatureError as exc:
            raise WebhookProcessingError("invalid_signature") from exc
        except IgnoredWebhookError:
            return "ignored"

        if not mark_webhook_seen(provider.provider_name, event.external_id):
            return "replay"

        PaymentWebhookService._apply_paid_event(event, provider_name=provider.provider_name)
        return "ok"

    @staticmethod
    def _apply_paid_event(event: PaymentEvent, *, provider_name: str) -> None:
        payment = (
            Payment.objects.select_related("order")
            .filter(external_id=event.external_id, provider=provider_name)
            .order_by("-id")
            .first()
        )
        if not payment:
            return

        if payment.status == Payment.STATUS_PAID and payment.order.status == Order.STATUS_PAID:
            return

        payment.webhook_payload = event.raw_payload
        payment.save(update_fields=["webhook_payload", "updated_at"])

        from apps.commerce.tasks import fulfill_order

        fulfill_order.delay(payment.id, paid_at_iso=_iso(event.paid_at))


def _iso(value) -> str | None:
    if value is None:
        return None
    return value.isoformat()


class PaymentSyncService:
    """Polling / Celery beat: подтянуть статусы pending у провайдера."""

    @staticmethod
    def sync_pending(*, older_than_seconds: int = 120, limit: int = 50) -> dict:
        cutoff = timezone.now() - timedelta(seconds=older_than_seconds)
        pending = (
            Payment.objects.select_related("order")
            .filter(status=Payment.STATUS_PENDING, created_at__lte=cutoff)
            .order_by("id")[:limit]
        )
        provider = get_payment_provider()
        paid = 0
        expired = 0

        for payment in pending:
            if not payment.external_id:
                continue
            if not hasattr(provider, "get_invoice_status"):
                continue
            try:
                status = provider.get_invoice_status(payment.external_id)
            except Exception:
                continue

            if status == "paid":
                from apps.commerce.tasks import fulfill_order

                fulfill_order.delay(payment.id)
                paid += 1
            elif status == "expired":
                PaymentSyncService._expire(payment)
                expired += 1

        now = timezone.now()
        for payment in Payment.objects.filter(
            status=Payment.STATUS_PENDING,
            expires_at__lt=now,
        ).select_related("order")[:limit]:
            PaymentSyncService._expire(payment)
            expired += 1

        return {"paid_queued": paid, "expired": expired}

    @staticmethod
    def _expire(payment: Payment) -> None:
        if payment.status != Payment.STATUS_PENDING:
            return
        payment.status = Payment.STATUS_EXPIRED
        payment.save(update_fields=["status", "updated_at"])
        order = payment.order
        if order.status == Order.STATUS_PENDING:
            order.status = Order.STATUS_EXPIRED
            order.save(update_fields=["status", "updated_at"])
        AuditLogger.record(
            actor=None,
            action="payment_expired",
            target_type="payment",
            target_id=payment.pk,
            new_value={"order_id": order.pk, "external_id": payment.external_id},
        )
