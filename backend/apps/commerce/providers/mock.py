import hashlib
import hmac
import uuid
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

from apps.commerce.providers.base import PaymentIntent


class MockCryptoProvider:
    """Тестовый провайдер: invoice без внешнего API."""

    provider_name = "mock"

    def create_invoice(self, order, amount_usd: Decimal, description: str) -> PaymentIntent:
        external_id = f"mock-{order.id}-{uuid.uuid4().hex[:8]}"
        expires_at = timezone.now() + timedelta(
            minutes=getattr(settings, "CRYPTOBOT_INVOICE_TTL_MINUTES", 60)
        )
        return PaymentIntent(
            external_id=external_id,
            payment_url=f"https://pay.mock/invoice/{external_id}",
            amount_usd=amount_usd,
            asset="USDT",
            expires_at=expires_at,
            instructions="Mock payment — подтвердите через webhook или admin.",
        )

    def get_invoice_status(self, external_id: str) -> str:
        return "pending"


def sign_cryptobot_body(api_token: str, raw_body: str) -> str:
    secret = hashlib.sha256(api_token.encode("utf-8")).digest()
    return hmac.new(secret, raw_body.encode("utf-8"), hashlib.sha256).hexdigest()


def check_cryptobot_signature(api_token: str, raw_body: str, headers) -> bool:
    received = ""
    if hasattr(headers, "get"):
        received = headers.get("crypto-pay-api-signature") or headers.get(
            "Crypto-Pay-Api-Signature", ""
        )
    if not received:
        return False
    expected = sign_cryptobot_body(api_token, raw_body)
    return hmac.compare_digest(expected, received)
