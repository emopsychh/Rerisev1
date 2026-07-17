from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from apps.ledger.constants import (
    ENTRY_TYPE_BINARY_BONUS,
    ENTRY_TYPE_PERSONAL_BONUS,
    ENTRY_TYPE_WITHDRAWAL,
)
from apps.ledger.models import Entry
from apps.ledger.services import LedgerError, LedgerWriter
from apps.users.models import User
from apps.wallet.models import Balance, SavedAddress, WithdrawalRequest
from apps.wallet.services import WalletUpdater, WithdrawalService, WithdrawalValidationError
from tests.support import AuthStoreTestMixin, DEFAULT_TEST_PASSWORD


class LedgerWriterTests(TestCase):
    def setUp(self):
        call_command("seed_ledger_rules")
        self.user = User.objects.create_user(
            email="ledger@test.com",
            password=DEFAULT_TEST_PASSWORD,
        )

    def test_credit_creates_entry_and_refreshes_balance(self):
        LedgerWriter.credit(
            self.user,
            ENTRY_TYPE_PERSONAL_BONUS,
            Decimal("150.00"),
            idempotency_key="test:bonus:1",
        )
        WalletUpdater.refresh(self.user)

        balance = Balance.objects.get(user=self.user)
        self.assertEqual(balance.available_usd, Decimal("150.00"))
        self.assertEqual(balance.total_earned_usd, Decimal("150.00"))
        self.assertEqual(Entry.objects.filter(user=self.user).count(), 1)

    def test_idempotent_credit_does_not_duplicate(self):
        LedgerWriter.credit(
            self.user,
            ENTRY_TYPE_PERSONAL_BONUS,
            Decimal("50.00"),
            idempotency_key="test:bonus:dup",
        )
        LedgerWriter.credit(
            self.user,
            ENTRY_TYPE_PERSONAL_BONUS,
            Decimal("50.00"),
            idempotency_key="test:bonus:dup",
        )
        self.assertEqual(Entry.objects.filter(user=self.user).count(), 1)

    def test_debit_reduces_available_balance(self):
        LedgerWriter.credit(self.user, ENTRY_TYPE_BINARY_BONUS, Decimal("200.00"))
        LedgerWriter.debit(self.user, ENTRY_TYPE_WITHDRAWAL, Decimal("50.00"))
        WalletUpdater.refresh(self.user)

        balance = Balance.objects.get(user=self.user)
        self.assertEqual(balance.available_usd, Decimal("150.00"))

    def test_idempotency_mismatch_raises_error(self):
        LedgerWriter.credit(
            self.user,
            ENTRY_TYPE_PERSONAL_BONUS,
            Decimal("50.00"),
            idempotency_key="test:bonus:mismatch",
        )
        with self.assertRaises(LedgerError):
            LedgerWriter.credit(
                self.user,
                ENTRY_TYPE_BINARY_BONUS,
                Decimal("50.00"),
                idempotency_key="test:bonus:mismatch",
            )

    def test_mark_paid_creates_ledger_debit(self):
        admin = User.objects.create_user(
            email="admin@test.com",
            password=DEFAULT_TEST_PASSWORD,
            is_staff=True,
        )
        LedgerWriter.credit(self.user, ENTRY_TYPE_PERSONAL_BONUS, Decimal("300.00"))
        WalletUpdater.refresh(self.user)

        request = WithdrawalService.create_request(
            user=self.user,
            amount_usd=Decimal("200.00"),
            usdt_address="TXyz123",
            network="TRC20",
        )
        WithdrawalService.mark_paid(request, reviewed_by=admin)
        WalletUpdater.refresh(self.user)

        balance = Balance.objects.get(user=self.user)
        self.assertEqual(balance.available_usd, Decimal("100.00"))
        self.assertEqual(balance.pending_usd, Decimal("0.00"))
        self.assertEqual(
            Entry.objects.filter(user=self.user, entry_type=ENTRY_TYPE_WITHDRAWAL).count(),
            1,
        )

    def test_second_withdraw_respects_pending_balance(self):
        LedgerWriter.credit(self.user, ENTRY_TYPE_PERSONAL_BONUS, Decimal("300.00"))
        WalletUpdater.refresh(self.user)

        WithdrawalService.create_request(
            user=self.user,
            amount_usd=Decimal("200.00"),
            usdt_address="TXyz123",
            network="TRC20",
        )
        with self.assertRaises(WithdrawalValidationError):
            WithdrawalService.create_request(
                user=self.user,
                amount_usd=Decimal("200.00"),
                usdt_address="TXyz456",
                network="TRC20",
            )


class WalletApiTests(AuthStoreTestMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        call_command("seed_ledger_rules")
        self.register_user("wallet@test.com")
        self.user = User.objects.get(email="wallet@test.com")
        LedgerWriter.credit(self.user, ENTRY_TYPE_PERSONAL_BONUS, Decimal("500.00"))
        WalletUpdater.refresh(self.user)
        self.login_user("wallet@test.com")

    def test_get_wallet_overview(self):
        response = self.client.get("/api/v1/wallet")
        self.assertEqual(response.status_code, 200)
        data = response.data["data"]
        self.assertEqual(data["balance"]["available_usd"], 500.0)
        self.assertEqual(data["withdrawal_limits"]["min_usd"], 100)
        self.assertEqual(len(data["recent_transactions"]), 1)

    def test_withdraw_creates_pending_request(self):
        response = self.client.post(
            "/api/v1/wallet/withdraw",
            {
                "amount_usd": "200.00",
                "usdt_address": "TXyz123wallet",
                "network": "TRC20",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["status"], "pending")

        balance = Balance.objects.get(user=self.user)
        self.assertEqual(balance.available_usd, Decimal("300.00"))
        self.assertEqual(balance.pending_usd, Decimal("200.00"))
        self.assertEqual(WithdrawalRequest.objects.count(), 1)
        self.assertTrue(
            SavedAddress.objects.filter(user=self.user, is_default=True).exists()
        )

    def test_withdraw_below_minimum_returns_422(self):
        response = self.client.post(
            "/api/v1/wallet/withdraw",
            {
                "amount_usd": "50.00",
                "usdt_address": "TXyz123wallet",
                "network": "TRC20",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.data["error"]["code"], "BUSINESS_RULE_ERROR")

    def test_withdraw_exceeds_available_returns_422(self):
        response = self.client.post(
            "/api/v1/wallet/withdraw",
            {
                "amount_usd": "600.00",
                "usdt_address": "TXyz123wallet",
                "network": "TRC20",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 422)

    def test_save_address(self):
        response = self.client.put(
            "/api/v1/wallet/address",
            {"address": "TNewAddress123", "network": "TRC20"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["address"], "TNewAddress123")

        overview = self.client.get("/api/v1/wallet")
        self.assertEqual(
            overview.data["data"]["saved_address"]["address"],
            "TNewAddress123",
        )

    def test_transactions_list(self):
        LedgerWriter.credit(self.user, ENTRY_TYPE_BINARY_BONUS, Decimal("10.00"))
        WalletUpdater.refresh(self.user)

        response = self.client.get("/api/v1/wallet/transactions?type=bonus")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["meta"]["total"], 2)
        self.assertEqual(len(response.data["data"]), 2)
