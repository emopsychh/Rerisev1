from django.core.management import call_command

from apps.commerce.models import Payment
from apps.commerce.services import PaymentConfirmationService

DEFAULT_TEST_PASSWORD = "password123"


class AuthStoreTestMixin:
    def seed_store(self):
        call_command("seed_commerce")
        call_command("seed_ledger_rules")

    def register_user(self, email: str, **extra):
        payload = {"email": email, "password": DEFAULT_TEST_PASSWORD, **extra}
        return self.client.post("/api/v1/auth/register", payload, format="json")

    def login_user(self, email: str):
        response = self.client.post(
            "/api/v1/auth/login",
            {"email": email, "password": DEFAULT_TEST_PASSWORD},
            format="json",
        )
        token = response.data["data"]["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def buy_tariff(self, product_id: str = "rise", order_type: str = "purchase"):
        response = self.client.post(
            "/api/v1/store/orders",
            {"product_id": product_id, "order_type": order_type},
            format="json",
        )
        payment = Payment.objects.get(order_id=response.data["data"]["order_id"])
        PaymentConfirmationService.confirm(payment)
        return response
