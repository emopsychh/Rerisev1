import json
from datetime import timedelta
from unittest.mock import patch

from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.commerce.models import Order, Payment, Subscription
from apps.commerce.providers.mock import sign_cryptobot_body
from apps.commerce.webhook_service import PaymentSyncService
from apps.users.services import UserRegistrationService
from tests.support import DEFAULT_TEST_PASSWORD


@override_settings(
    PAYMENT_PROVIDER="mock",
    CRYPTOBOT_API_TOKEN="test-token",
    CRYPTOBOT_WEBHOOK_SECRET_PATH="wh-secret",
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class CryptoBotWebhookTests(TestCase):
    def setUp(self):
        cache.clear()
        from django.core.management import call_command

        call_command("seed_commerce")
        call_command("seed_ledger_rules")
        self.api = APIClient()
        self.client = Client()
        self.user = UserRegistrationService.register(
            email="pay@rerise.ai",
            password=DEFAULT_TEST_PASSWORD,
            first_name="Pay",
        )
        login = self.api.post(
            "/api/v1/auth/login",
            {"email": "pay@rerise.ai", "password": DEFAULT_TEST_PASSWORD},
            format="json",
        )
        self.api.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login.data['data']['access_token']}"
        )

    def _create_order(self):
        response = self.api.post(
            "/api/v1/store/orders",
            {"product_id": "rise", "order_type": "purchase"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        order_id = response.data["data"]["order_id"]
        payment = Payment.objects.get(order_id=order_id)
        # Webhook ищет provider=cryptobot — подменим для TC
        payment.provider = "cryptobot"
        payment.external_id = "inv-1001"
        payment.save(update_fields=["provider", "external_id", "updated_at"])
        return payment

    def _signed_post(self, body: dict, *, secret="wh-secret", token="test-token"):
        raw = json.dumps(body, separators=(",", ":"))
        signature = sign_cryptobot_body(token, raw)
        return self.client.post(
            f"/api/v1/store/webhook/cryptobot/{secret}",
            data=raw,
            content_type="application/json",
            headers={"crypto-pay-api-signature": signature},
        )

    def test_webhook_paid_fulfills_order(self):
        payment = self._create_order()
        response = self._signed_post(
            {
                "update_id": 1,
                "update_type": "invoice_paid",
                "payload": {
                    "invoice_id": "inv-1001",
                    "status": "paid",
                    "paid_at": timezone.now().isoformat(),
                },
            }
        )
        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.STATUS_PAID)
        self.assertEqual(payment.order.status, Order.STATUS_PAID)
        self.assertTrue(
            Subscription.objects.filter(user=self.user, tariff_id="rise").exists()
        )

    def test_webhook_replay_is_idempotent(self):
        payment = self._create_order()
        body = {
            "update_id": 2,
            "update_type": "invoice_paid",
            "payload": {"invoice_id": "inv-1001", "status": "paid"},
        }
        first = self._signed_post(body)
        second = self._signed_post(body)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()["result"], "replay")
        self.assertEqual(Order.objects.filter(status=Order.STATUS_PAID).count(), 1)

    def test_invalid_signature_returns_400(self):
        self._create_order()
        raw = json.dumps(
            {
                "update_type": "invoice_paid",
                "payload": {"invoice_id": "inv-1001"},
            }
        )
        response = self.client.post(
            "/api/v1/store/webhook/cryptobot/wh-secret",
            data=raw,
            content_type="application/json",
            headers={"crypto-pay-api-signature": "bad-signature"},
        )
        self.assertEqual(response.status_code, 400)

    def test_wrong_secret_path_returns_404(self):
        response = self._signed_post(
            {"update_type": "invoice_paid", "payload": {"invoice_id": "x"}},
            secret="wrong",
        )
        self.assertEqual(response.status_code, 404)

    def test_ignored_update_type(self):
        response = self._signed_post(
            {"update_type": "invoice_expired", "payload": {"invoice_id": "inv-1001"}}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["result"], "ignored")


@override_settings(PAYMENT_PROVIDER="mock", CELERY_TASK_ALWAYS_EAGER=True)
class PaymentSyncTests(TestCase):
    def setUp(self):
        from django.core.management import call_command

        call_command("seed_commerce")
        call_command("seed_ledger_rules")
        self.user = UserRegistrationService.register(
            email="sync@rerise.ai",
            password=DEFAULT_TEST_PASSWORD,
        )

    def test_expire_by_ttl(self):
        from apps.commerce.models import Product

        product = Product.objects.get(slug="rise")
        order = Order.objects.create(
            user=self.user,
            product=product,
            amount_usd=product.price_usd,
            status=Order.STATUS_PENDING,
            order_type=Order.TYPE_PURCHASE,
        )
        Payment.objects.create(
            order=order,
            provider="mock",
            external_id="mock-expired",
            amount_usd=product.price_usd,
            currency_crypto="USDT",
            status=Payment.STATUS_PENDING,
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        result = PaymentSyncService.sync_pending(older_than_seconds=0)
        self.assertGreaterEqual(result["expired"], 1)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_EXPIRED)

    def test_sync_paid_from_provider(self):
        from apps.commerce.models import Product

        product = Product.objects.get(slug="rise")
        order = Order.objects.create(
            user=self.user,
            product=product,
            amount_usd=product.price_usd,
            status=Order.STATUS_PENDING,
            order_type=Order.TYPE_PURCHASE,
        )
        payment = Payment.objects.create(
            order=order,
            provider="mock",
            external_id="mock-paid-1",
            amount_usd=product.price_usd,
            currency_crypto="USDT",
            status=Payment.STATUS_PENDING,
            created_at=timezone.now() - timedelta(minutes=5),
        )
        Payment.objects.filter(pk=payment.pk).update(
            created_at=timezone.now() - timedelta(minutes=5)
        )

        with patch(
            "apps.commerce.providers.mock.MockCryptoProvider.get_invoice_status",
            return_value="paid",
        ):
            result = PaymentSyncService.sync_pending(older_than_seconds=60)

        self.assertEqual(result["paid_queued"], 1)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_PAID)


@override_settings(PAYMENT_PROVIDER="mock")
class MockProviderOrderTests(TestCase):
    def setUp(self):
        from django.core.management import call_command

        call_command("seed_commerce")
        self.client = APIClient()
        UserRegistrationService.register(
            email="mockpay@rerise.ai",
            password=DEFAULT_TEST_PASSWORD,
        )
        login = self.client.post(
            "/api/v1/auth/login",
            {"email": "mockpay@rerise.ai", "password": DEFAULT_TEST_PASSWORD},
            format="json",
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login.data['data']['access_token']}"
        )

    def test_create_order_returns_payment_url(self):
        response = self.client.post(
            "/api/v1/store/orders",
            {"product_id": "rise", "order_type": "purchase"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        payment = response.data["data"]["payment"]
        self.assertEqual(payment["provider"], "mock")
        self.assertTrue(payment["payment_url"])
