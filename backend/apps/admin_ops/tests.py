from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from apps.admin_ops.models import AuditLog
from apps.admin_ops.services import AdminAdjustmentService, UserModerationService
from apps.commerce.models import Payment
from apps.ledger.constants import DIRECTION_CREDIT, ENTRY_TYPE_PERSONAL_BONUS
from apps.ledger.services import LedgerWriter
from apps.users.models import User
from apps.users.services import UserRegistrationService
from apps.wallet.models import Balance, WithdrawalRequest
from apps.wallet.services import WalletUpdater, WithdrawalService
from tests.support import AuthStoreTestMixin, DEFAULT_TEST_PASSWORD


class AdminOpsApiTests(TestCase):
    def setUp(self):
        call_command("seed_ledger_rules")
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            email="admin@rerise.ai",
            password=DEFAULT_TEST_PASSWORD,
        )
        self.user = UserRegistrationService.register(
            email="member@rerise.ai",
            password=DEFAULT_TEST_PASSWORD,
            first_name="Member",
        )
        self.client.force_authenticate(user=self.admin)

    def test_create_adjustment_and_audit(self):
        response = self.client.post(
            "/api/v1/admin/ledger/adjustments",
            {
                "user_id": self.user.pk,
                "amount_usd": "50.00",
                "direction": DIRECTION_CREDIT,
                "reason": "Компенсация",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            AuditLog.objects.filter(action="ledger_adjustment", target_id=self.user.pk).exists()
        )
        balance = Balance.objects.get(user=self.user)
        self.assertEqual(balance.available_usd, Decimal("50.00"))

    def test_block_user_prevents_login(self):
        response = self.client.post(
            f"/api/v1/admin/users/{self.user.pk}/block",
            {"reason": "fraud"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

        guest = APIClient()
        login = guest.post(
            "/api/v1/auth/login",
            {"email": "member@rerise.ai", "password": DEFAULT_TEST_PASSWORD},
            format="json",
        )
        self.assertEqual(login.status_code, 401)

    def test_approve_and_pay_withdrawal(self):
        LedgerWriter.credit(self.user, ENTRY_TYPE_PERSONAL_BONUS, Decimal("200.00"))
        WalletUpdater.refresh(self.user)
        withdrawal = WithdrawalService.create_request(
            self.user,
            Decimal("100.00"),
            "TAdminTestAddress",
            "TRC20",
        )

        approve = self.client.patch(
            f"/api/v1/admin/withdrawals/{withdrawal.pk}",
            {"status": "approved"},
            format="json",
        )
        self.assertEqual(approve.status_code, 200)
        self.assertEqual(approve.data["data"]["status"], "approved")

        paid = self.client.patch(
            f"/api/v1/admin/withdrawals/{withdrawal.pk}",
            {"status": "paid", "tx_hash": "0xabc"},
            format="json",
        )
        self.assertEqual(paid.status_code, 200)
        self.assertEqual(paid.data["data"]["status"], "paid")
        self.assertTrue(
            AuditLog.objects.filter(action="withdrawal_paid", target_id=withdrawal.pk).exists()
        )

    def test_reject_stores_reason(self):
        LedgerWriter.credit(self.user, ENTRY_TYPE_PERSONAL_BONUS, Decimal("200.00"))
        WalletUpdater.refresh(self.user)
        withdrawal = WithdrawalService.create_request(
            self.user,
            Decimal("100.00"),
            "TRejectAddress",
            "TRC20",
        )
        response = self.client.patch(
            f"/api/v1/admin/withdrawals/{withdrawal.pk}",
            {"status": "rejected", "reason": "Неверный адрес"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        withdrawal.refresh_from_db()
        self.assertEqual(withdrawal.status, "rejected")
        self.assertEqual(withdrawal.rejection_reason, "Неверный адрес")

    def test_cannot_block_self(self):
        response = self.client.post(
            f"/api/v1/admin/users/{self.admin.pk}/block",
            {"reason": "oops"},
            format="json",
        )
        self.assertEqual(response.status_code, 422)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_audit_log_list(self):
        AdminAdjustmentService.apply(
            self.user,
            amount_usd="10",
            direction=DIRECTION_CREDIT,
            reason="test",
            actor=self.admin,
        )
        response = self.client.get("/api/v1/admin/audit-log")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data["data"]), 1)


class EndToEndJourneyTests(AuthStoreTestMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        call_command("seed_demo")

    def test_user_journey_register_buy_home_crm_withdraw(self):
        register = self.register_user(
            "journey@rerise.ai",
            first_name="Journey",
            last_name="User",
        )
        self.assertEqual(register.status_code, 201)
        self.login_user("journey@rerise.ai")

        buy = self.buy_tariff("rise")
        self.assertEqual(buy.status_code, 201)
        self.assertEqual(Payment.objects.filter(status="paid").count(), 1)

        home = self.client.get("/api/v1/home")
        self.assertEqual(home.status_code, 200)
        self.assertIn("next_action", home.data["data"])

        programs = self.client.get("/api/v1/programs")
        self.assertEqual(programs.status_code, 200)

        crm = self.client.post(
            "/api/v1/crm/leads",
            {"name": "Лид", "contact": "@lead", "source": "referral"},
            format="json",
        )
        self.assertEqual(crm.status_code, 201)

        user = User.objects.get(email="journey@rerise.ai")
        LedgerWriter.credit(user, ENTRY_TYPE_PERSONAL_BONUS, Decimal("150.00"))
        WalletUpdater.refresh(user)

        withdraw = self.client.post(
            "/api/v1/wallet/withdraw",
            {
                "amount_usd": "100.00",
                "usdt_address": "TJourneyWithdraw",
                "network": "TRC20",
            },
            format="json",
        )
        self.assertEqual(withdraw.status_code, 201)
        self.assertEqual(WithdrawalRequest.objects.filter(user=user).count(), 1)

        wallet = self.client.get("/api/v1/wallet")
        self.assertEqual(wallet.status_code, 200)
        self.assertEqual(wallet.data["data"]["balance"]["pending_usd"], 100.0)


class SeedDemoCommandTests(TestCase):
    def test_seed_demo_runs(self):
        call_command("seed_demo")
        from apps.commerce.models import Product
        from apps.crm.models import LeadStage

        self.assertGreaterEqual(Product.objects.count(), 3)
        self.assertEqual(LeadStage.objects.count(), 4)


class UserModerationServiceTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email="ops@rerise.ai",
            password=DEFAULT_TEST_PASSWORD,
        )
        self.user = UserRegistrationService.register(
            email="blocked@rerise.ai",
            password=DEFAULT_TEST_PASSWORD,
        )

    def test_block_unblock_writes_audit(self):
        UserModerationService.block(self.user, actor=self.admin, reason="test")
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        UserModerationService.unblock(self.user, actor=self.admin)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertEqual(AuditLog.objects.filter(target_type="user").count(), 2)
