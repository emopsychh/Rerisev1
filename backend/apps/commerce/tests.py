from django.core.management import call_command
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.commerce.models import Order, Payment, Subscription
from apps.commerce.services import PaymentConfirmationService
from apps.users.services import UserRegistrationService


class CommerceAPITestCase(TestCase):
    def setUp(self):
        call_command("seed_commerce")
        call_command("seed_ledger_rules")
        self.client = APIClient()
        self.user = UserRegistrationService.register(
            email="buyer@rerise.ai",
            password="password123",
            first_name="Покупатель",
        )
        self.auth = self._auth_headers("buyer@rerise.ai")

    def _auth_headers(self, email: str):
        response = self.client.post(
            "/api/v1/auth/login",
            {"email": email, "password": "password123"},
            format="json",
        )
        token = response.data["data"]["access_token"]
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def _create_and_confirm(self, product_id: str, order_type: str = "purchase"):
        self.client.credentials(**self.auth)
        create = self.client.post(
            "/api/v1/store/orders",
            {"product_id": product_id, "order_type": order_type},
            format="json",
        )
        payment = Payment.objects.get(order_id=create.data["data"]["order_id"])
        PaymentConfirmationService.confirm(payment)
        return create

    def test_get_tariffs_public(self):
        response = self.client.get("/api/v1/store/tariffs")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tariffs = response.data["data"]
        self.assertEqual(len(tariffs), 3)
        self.assertEqual(tariffs[0]["id"], "rise")
        self.assertEqual(tariffs[1]["price_usd"], 300.0)

    def test_get_tokens_authenticated(self):
        self.client.credentials(**self.auth)
        response = self.client.get("/api/v1/store/tokens")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["balance"], 0)
        self.assertEqual(len(response.data["data"]["packs"]), 2)

    def test_create_order_rise(self):
        self.client.credentials(**self.auth)
        response = self.client.post(
            "/api/v1/store/orders",
            {"product_id": "rise-pro", "order_type": "purchase"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data["data"]
        self.assertEqual(data["status"], "pending")
        self.assertEqual(data["payment"]["provider"], "manual")
        self.assertIn("instructions", data["payment"])

    def test_duplicate_pending_expires_old(self):
        self.client.credentials(**self.auth)
        first = self.client.post(
            "/api/v1/store/orders",
            {"product_id": "rise", "order_type": "purchase"},
            format="json",
        )
        second = self.client.post(
            "/api/v1/store/orders",
            {"product_id": "rise", "order_type": "purchase"},
            format="json",
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)

        old_order = Order.objects.get(pk=first.data["data"]["order_id"])
        self.assertEqual(old_order.status, "expired")

    def test_manual_confirm_fulfills_order(self):
        self.client.credentials(**self.auth)
        create = self.client.post(
            "/api/v1/store/orders",
            {"product_id": "rise", "order_type": "purchase"},
            format="json",
        )
        order_id = create.data["data"]["order_id"]
        payment = Payment.objects.get(order_id=order_id)

        PaymentConfirmationService.confirm(payment)

        order = Order.objects.get(pk=order_id)
        self.assertEqual(order.status, "paid")
        self.assertTrue(Subscription.objects.filter(user=self.user, tariff_id="rise").exists())

    def test_me_subscription_after_purchase(self):
        self.client.credentials(**self.auth)
        create = self.client.post(
            "/api/v1/store/orders",
            {"product_id": "rise-pro", "order_type": "purchase"},
            format="json",
        )
        payment = Payment.objects.get(order_id=create.data["data"]["order_id"])
        PaymentConfirmationService.confirm(payment)

        me = self.client.get("/api/v1/me")
        subscription = me.data["data"]["subscription"]
        self.assertIsNotNone(subscription)
        self.assertEqual(subscription["tariff_id"], "rise-pro")
        self.assertEqual(subscription["tariff_name"], "Rise Pro")
        self.assertTrue(subscription["is_active"])

    def test_purchase_rejected_when_active_tariff(self):
        self.client.credentials(**self.auth)
        first = self.client.post(
            "/api/v1/store/orders",
            {"product_id": "rise", "order_type": "purchase"},
            format="json",
        )
        PaymentConfirmationService.confirm(
            Payment.objects.get(order_id=first.data["data"]["order_id"])
        )

        second = self.client.post(
            "/api/v1/store/orders",
            {"product_id": "rise-pro", "order_type": "purchase"},
            format="json",
        )
        self.assertEqual(second.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_upgrade_rise_to_pro(self):
        self.client.credentials(**self.auth)
        purchase = self.client.post(
            "/api/v1/store/orders",
            {"product_id": "rise", "order_type": "purchase"},
            format="json",
        )
        PaymentConfirmationService.confirm(
            Payment.objects.get(order_id=purchase.data["data"]["order_id"])
        )

        upgrade = self.client.post(
            "/api/v1/store/orders",
            {"product_id": "rise-pro", "order_type": "upgrade"},
            format="json",
        )
        self.assertEqual(upgrade.status_code, status.HTTP_201_CREATED)
        PaymentConfirmationService.confirm(
            Payment.objects.get(order_id=upgrade.data["data"]["order_id"])
        )

        subscription = Subscription.objects.get(user=self.user)
        self.assertEqual(subscription.tariff_id, "rise-pro")

    def test_renewal_requires_tariff(self):
        self.client.credentials(**self.auth)
        response = self.client.post(
            "/api/v1/store/orders",
            {"product_id": "subscription", "order_type": "renewal"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_upgrade_preserves_active_until(self):
        self._create_and_confirm("rise")
        subscription = Subscription.objects.get(user=self.user)
        active_until_before = subscription.active_until

        self.client.credentials(**self.auth)
        upgrade = self.client.post(
            "/api/v1/store/orders",
            {"product_id": "rise-pro", "order_type": "upgrade"},
            format="json",
        )
        payment = Payment.objects.get(order_id=upgrade.data["data"]["order_id"])
        PaymentConfirmationService.confirm(payment)

        subscription.refresh_from_db()
        self.assertEqual(subscription.tariff_id, "rise-pro")
        self.assertEqual(subscription.active_until, active_until_before)

    def test_confirm_payment_is_idempotent(self):
        self.client.credentials(**self.auth)
        create = self.client.post(
            "/api/v1/store/orders",
            {"product_id": "rise", "order_type": "purchase"},
            format="json",
        )
        payment = Payment.objects.get(order_id=create.data["data"]["order_id"])

        PaymentConfirmationService.confirm(payment)
        PaymentConfirmationService.confirm(payment)

        self.assertEqual(Subscription.objects.filter(user=self.user).count(), 1)
        self.assertEqual(Order.objects.get(pk=create.data["data"]["order_id"]).status, "paid")

    def test_get_order_after_paid(self):
        create = self._create_and_confirm("rise")
        order_id = create.data["data"]["order_id"]

        detail = self.client.get(f"/api/v1/store/orders/{order_id}")
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data["data"]["status"], "paid")
        self.assertEqual(detail.data["data"]["granted_access"]["tariff"], "rise")

        listing = self.client.get("/api/v1/store/orders")
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(listing.data["data"]), 1)
        self.assertEqual(listing.data["data"][0]["id"], order_id)
        self.assertIn("product_name", listing.data["data"][0])
        self.assertIn("status_label", listing.data["data"][0])

    def test_token_pack_pays_from_wallet_instantly(self):
        from decimal import Decimal

        from apps.ibox.tokens import TokenService
        from apps.ledger.constants import ENTRY_TYPE_ADJUSTMENT
        from apps.ledger.services import LedgerWriter
        from apps.wallet.services import WalletUpdater

        LedgerWriter.credit(
            self.user,
            ENTRY_TYPE_ADJUSTMENT,
            Decimal("50.00"),
            description="Тестовое пополнение",
            idempotency_key="test-wallet-topup-tokens",
        )
        WalletUpdater.refresh(self.user)

        before_tokens = TokenService.get_available(self.user)
        self.client.credentials(**self.auth)
        response = self.client.post(
            "/api/v1/store/orders",
            {"product_id": "tokens-1000", "order_type": "purchase"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data["data"]
        self.assertEqual(data["status"], "paid")
        self.assertEqual(data["payment"]["provider"], "wallet")
        self.assertIsNone(data["payment"]["payment_url"])
        self.assertEqual(TokenService.get_available(self.user), before_tokens + 1000)

        balance = WalletUpdater.refresh(self.user)
        self.assertEqual(balance.available_usd, Decimal("40.00"))

    def test_tariff_pays_from_wallet_instantly(self):
        from decimal import Decimal

        from apps.ledger.constants import ENTRY_TYPE_ADJUSTMENT
        from apps.ledger.services import LedgerWriter
        from apps.partner.models import PartnerProfile
        from apps.wallet.services import WalletUpdater

        LedgerWriter.credit(
            self.user,
            ENTRY_TYPE_ADJUSTMENT,
            Decimal("100.00"),
            description="Тестовое пополнение под тариф",
            idempotency_key="test-wallet-topup-tariff",
        )
        WalletUpdater.refresh(self.user)

        self.client.credentials(**self.auth)
        response = self.client.post(
            "/api/v1/store/orders",
            {"product_id": "rise", "order_type": "purchase"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data["data"]
        self.assertEqual(data["status"], "paid")
        self.assertEqual(data["payment"]["provider"], "wallet")
        self.assertIsNone(data["payment"]["payment_url"])

        partner = PartnerProfile.objects.filter(user=self.user).first()
        self.assertIsNotNone(partner)
        self.assertTrue(partner.is_active)
        self.assertEqual(partner.tariff_id, "rise")

        balance = WalletUpdater.refresh(self.user)
        self.assertEqual(balance.available_usd, Decimal("10.00"))

    def test_wallet_pay_creates_store_purchase_entry(self):
        from decimal import Decimal

        from apps.ledger.constants import ENTRY_TYPE_STORE_PURCHASE, DIRECTION_DEBIT
        from apps.ledger.models import Entry
        from apps.ledger.constants import ENTRY_TYPE_ADJUSTMENT
        from apps.ledger.services import LedgerWriter
        from apps.wallet.services import WalletUpdater

        LedgerWriter.credit(
            self.user,
            ENTRY_TYPE_ADJUSTMENT,
            Decimal("100.00"),
            description="topup",
            idempotency_key="topup-store-entry",
        )
        WalletUpdater.refresh(self.user)

        self.client.credentials(**self.auth)
        response = self.client.post(
            "/api/v1/store/orders",
            {"product_id": "rise", "order_type": "purchase"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order_id = response.data["data"]["order_id"]
        debit = Entry.objects.get(
            user=self.user,
            entry_type=ENTRY_TYPE_STORE_PURCHASE,
            direction=DIRECTION_DEBIT,
            idempotency_key=f"store-purchase:{order_id}",
        )
        self.assertEqual(debit.amount, Decimal("90.00"))

    def test_manual_confirm_does_not_debit_wallet(self):
        """Confirm Payment = внешняя оплата; кошелёк не трогаем."""
        from decimal import Decimal

        from apps.ledger.constants import ENTRY_TYPE_ADJUSTMENT, ENTRY_TYPE_STORE_PURCHASE
        from apps.ledger.models import Entry
        from apps.ledger.services import LedgerWriter
        from apps.wallet.services import WalletUpdater

        # Баланса не хватает на Rise → уйдёт в manual pending
        LedgerWriter.credit(
            self.user,
            ENTRY_TYPE_ADJUSTMENT,
            Decimal("10.00"),
            description="small",
            idempotency_key="topup-small-manual",
        )
        WalletUpdater.refresh(self.user)

        self.client.credentials(**self.auth)
        response = self.client.post(
            "/api/v1/store/orders",
            {"product_id": "rise", "order_type": "purchase"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["status"], "pending")
        order_id = response.data["data"]["order_id"]

        # Пополнили кошелёк ПОСЛЕ создания заказа — confirm всё равно не должен списать
        LedgerWriter.credit(
            self.user,
            ENTRY_TYPE_ADJUSTMENT,
            Decimal("200.00"),
            description="later",
            idempotency_key="topup-later-manual",
        )
        WalletUpdater.refresh(self.user)

        from apps.commerce.models import Payment
        from apps.commerce.services import PaymentConfirmationService

        payment = Payment.objects.get(order_id=order_id)
        PaymentConfirmationService.confirm(payment)

        self.assertFalse(
            Entry.objects.filter(
                user=self.user,
                entry_type=ENTRY_TYPE_STORE_PURCHASE,
            ).exists()
        )
        self.assertEqual(WalletUpdater.refresh(self.user).available_usd, Decimal("210.00"))

    def test_second_wallet_purchase_fails_when_insufficient(self):
        from decimal import Decimal

        from apps.ledger.constants import ENTRY_TYPE_ADJUSTMENT
        from apps.ledger.services import LedgerWriter
        from apps.wallet.services import WalletUpdater

        LedgerWriter.credit(
            self.user,
            ENTRY_TYPE_ADJUSTMENT,
            Decimal("100.00"),
            description="only-100",
            idempotency_key="topup-100-once",
        )
        WalletUpdater.refresh(self.user)

        self.client.credentials(**self.auth)
        first = self.client.post(
            "/api/v1/store/orders",
            {"product_id": "rise", "order_type": "purchase"},
            format="json",
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(first.data["data"]["status"], "paid")

        # Уже есть тариф — апгрейд на pro ($300) при остатке $10 → pending или 422
        second = self.client.post(
            "/api/v1/store/orders",
            {"product_id": "rise-pro", "order_type": "upgrade"},
            format="json",
        )
        # Недостаточно для wallet → external pending (не paid)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.data["data"]["status"], "pending")
        self.assertNotEqual(second.data["data"]["payment"]["provider"], "wallet")
