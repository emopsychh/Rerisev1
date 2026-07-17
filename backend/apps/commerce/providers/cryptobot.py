import json
from datetime import datetime, timedelta
from decimal import Decimal

import httpx
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.commerce.providers.base import (
    IgnoredWebhookError,
    InvalidSignatureError,
    PaymentEvent,
    PaymentIntent,
    PaymentProviderError,
)
from apps.commerce.providers.mock import check_cryptobot_signature


class CryptoBotProvider:
    """Telegram Crypto Pay API (CryptoBot)."""

    provider_name = "cryptobot"

    def __init__(self, *, api_token: str | None = None, testnet: bool | None = None):
        self.api_token = api_token or settings.CRYPTOBOT_API_TOKEN
        if not self.api_token:
            raise PaymentProviderError(
                "CRYPTOBOT_API_TOKEN не задан. Укажите токен или PAYMENT_PROVIDER=manual."
            )
        use_testnet = (
            settings.CRYPTOBOT_TESTNET if testnet is None else testnet
        )
        self.base_url = (
            "https://testnet-pay.crypt.bot/api"
            if use_testnet
            else "https://pay.crypt.bot/api"
        )
        self.asset = getattr(settings, "CRYPTOBOT_ASSET", "USDT")
        self.invoice_ttl = int(getattr(settings, "CRYPTOBOT_INVOICE_TTL_MINUTES", 60))
        self.paid_btn_url = getattr(settings, "CRYPTOBOT_PAID_BTN_URL", "")

    def create_invoice(self, order, amount_usd: Decimal, description: str) -> PaymentIntent:
        payload = {
            "asset": self.asset,
            "amount": str(amount_usd),
            "description": description[:1024],
            "payload": json.dumps({"order_id": order.id}),
            "expires_in": self.invoice_ttl * 60,
        }
        if self.paid_btn_url:
            payload["paid_btn_name"] = "callback"
            payload["paid_btn_url"] = self.paid_btn_url.format(order_id=order.id)

        data = self._request("createInvoice", payload)
        invoice_id = str(data["invoice_id"])
        payment_url = data.get("bot_invoice_url") or data.get("pay_url") or data.get("mini_app_invoice_url")
        expires_at = self._parse_expires(data) or (
            timezone.now() + timedelta(minutes=self.invoice_ttl)
        )
        return PaymentIntent(
            external_id=invoice_id,
            payment_url=payment_url,
            amount_usd=amount_usd,
            asset=self.asset,
            expires_at=expires_at,
            instructions="Оплатите USDT через CryptoBot по ссылке.",
        )

    def get_invoice_status(self, external_id: str) -> str:
        data = self._request("getInvoices", {"invoice_ids": str(external_id)})
        items = data.get("items") or []
        if not items:
            return "pending"
        status = (items[0].get("status") or "pending").lower()
        if status == "paid":
            return "paid"
        if status in {"expired", "cancelled"}:
            return "expired"
        return "pending"

    def verify_webhook(self, raw_body: bytes, headers) -> PaymentEvent:
        raw_str = raw_body.decode("utf-8")
        if not check_cryptobot_signature(self.api_token, raw_str, headers):
            raise InvalidSignatureError("Невалидная подпись CryptoBot webhook")

        data = json.loads(raw_str)
        update_type = data.get("update_type")
        if update_type != "invoice_paid":
            raise IgnoredWebhookError(f"Ignored update_type={update_type}")

        payload = data.get("payload") or {}
        invoice_id = payload.get("invoice_id")
        if invoice_id is None:
            raise InvalidSignatureError("В webhook нет invoice_id")

        paid_at = self._parse_paid_at(payload.get("paid_at"))
        return PaymentEvent(
            external_id=str(invoice_id),
            status="paid",
            paid_at=paid_at,
            raw_payload=data,
        )

    def _request(self, method: str, params: dict) -> dict:
        url = f"{self.base_url}/{method}"
        headers = {"Crypto-Pay-API-Token": self.api_token}
        try:
            with httpx.Client(timeout=30.0) as client:
                # Crypto Pay accepts both GET query and POST JSON; use POST JSON.
                response = client.post(url, headers=headers, json=params)
        except httpx.HTTPError as exc:
            raise PaymentProviderError(f"CryptoBot network error: {exc}") from exc

        try:
            body = response.json()
        except ValueError as exc:
            raise PaymentProviderError(
                f"CryptoBot invalid JSON ({response.status_code})"
            ) from exc

        if not body.get("ok"):
            error = body.get("error") or body
            raise PaymentProviderError(f"CryptoBot API error: {error}")

        return body.get("result") or {}

    @staticmethod
    def _parse_expires(data: dict) -> datetime | None:
        raw = data.get("expiration_date") or data.get("expires_at")
        if not raw:
            return None
        if isinstance(raw, (int, float)):
            return datetime.fromtimestamp(raw, tz=timezone.get_current_timezone())
        parsed = parse_datetime(str(raw))
        if parsed and timezone.is_naive(parsed):
            return timezone.make_aware(parsed, timezone.utc)
        return parsed

    @staticmethod
    def _parse_paid_at(raw) -> datetime | None:
        if not raw:
            return timezone.now()
        if isinstance(raw, (int, float)):
            return datetime.fromtimestamp(raw, tz=timezone.utc)
        parsed = parse_datetime(str(raw))
        if parsed and timezone.is_naive(parsed):
            return timezone.make_aware(parsed, timezone.utc)
        return parsed or timezone.now()
