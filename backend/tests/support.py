from decimal import Decimal

from django.core.management import call_command

from apps.commerce.models import Payment
from apps.commerce.services import PaymentConfirmationService
from apps.ledger.constants import ENTRY_TYPE_ADJUSTMENT
from apps.ledger.services import LedgerWriter
from apps.users.models import User
from apps.wallet.services import WalletUpdater

DEFAULT_TEST_PASSWORD = "password123"


class AuthStoreTestMixin:
    def seed_store(self):
        call_command("seed_commerce")
        call_command("seed_ledger_rules")

    def register_user(self, email: str, **extra):
        self._auth_email = email
        payload = {"email": email, "password": DEFAULT_TEST_PASSWORD, **extra}
        return self.client.post("/api/v1/auth/register", payload, format="json")

    def login_user(self, email: str):
        self._auth_email = email
        response = self.client.post(
            "/api/v1/auth/login",
            {"email": email, "password": DEFAULT_TEST_PASSWORD},
            format="json",
        )
        token = response.data["data"]["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def fund_wallet(self, amount: str = "10000.00"):
        email = getattr(self, "_auth_email", None)
        if not email:
            raise RuntimeError("login_user/register_user before fund_wallet")
        user = User.objects.get(email=email)
        key = f"test-fund:{user.pk}:{amount}:{WalletUpdater.refresh(user).available_usd}"
        LedgerWriter.credit(
            user,
            ENTRY_TYPE_ADJUSTMENT,
            Decimal(amount),
            description="test-wallet-fund",
            idempotency_key=key,
        )
        WalletUpdater.refresh(user)

    def buy_tariff(self, product_id: str = "rise", order_type: str = "purchase"):
        self.fund_wallet("10000.00")
        response = self.client.post(
            "/api/v1/store/orders",
            {"product_id": product_id, "order_type": order_type},
            format="json",
        )
        if response.status_code >= 400:
            raise AssertionError(f"buy_tariff failed: {response.status_code} {response.data}")
        data = response.data["data"]
        if data.get("status") != "paid":
            payment = Payment.objects.get(order_id=data["order_id"])
            PaymentConfirmationService.confirm(payment)
        return response
