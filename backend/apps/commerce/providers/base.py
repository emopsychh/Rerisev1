from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol


@dataclass
class PaymentIntent:
    external_id: str
    payment_url: str | None
    amount_usd: Decimal
    asset: str
    expires_at: datetime
    instructions: str = ""


@dataclass
class PaymentEvent:
    external_id: str
    status: str
    paid_at: datetime | None
    raw_payload: dict


class InvalidSignatureError(ValueError):
    pass


class IgnoredWebhookError(ValueError):
    pass


class PaymentProviderError(ValueError):
    pass


class PaymentProvider(Protocol):
    provider_name: str

    def create_invoice(
        self,
        order,
        amount_usd: Decimal,
        description: str,
    ) -> PaymentIntent: ...

    def get_invoice_status(self, external_id: str) -> str: ...
