import uuid
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

from apps.commerce.providers.base import PaymentIntent


class ManualCryptoProvider:
    provider_name = "manual"

    def create_invoice(self, order, amount_usd: Decimal, description: str) -> PaymentIntent:
        external_id = f"manual-{order.id}-{uuid.uuid4().hex[:8]}"
        expires_at = timezone.now() + timedelta(
            minutes=settings.MANUAL_PAYMENT_TTL_MINUTES
        )
        instructions = settings.MANUAL_PAYMENT_INSTRUCTIONS.format(
            order_id=order.id,
            amount_usd=amount_usd,
        )
        return PaymentIntent(
            external_id=external_id,
            payment_url=None,
            amount_usd=amount_usd,
            asset="USDT",
            expires_at=expires_at,
            instructions=instructions,
        )

    def get_invoice_status(self, external_id: str) -> str:
        return "pending"
