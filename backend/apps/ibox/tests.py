from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from apps.commerce.models import Payment
from apps.commerce.services import PaymentConfirmationService
from apps.ibox.models import ChatSession, Scenario, TokenBalance, TokenTransaction
from apps.ibox.tokens import TokenService
from apps.users.models import User
from tests.support import AuthStoreTestMixin


@override_settings(STORE_WALLET_ONLY=False)
class IboxAPITestCase(AuthStoreTestMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.seed_store()
        call_command("seed_ibox")
        self.register_user("creator@rerise.ai", first_name="Креатор", last_name="Тест")
        self.login_user("creator@rerise.ai")
        self.buy_tariff("rise")

    def test_tariff_purchase_credits_tokens(self):
        balance = TokenBalance.objects.get(user__email="creator@rerise.ai")
        self.assertEqual(balance.available, 1000)
        self.assertTrue(
            TokenTransaction.objects.filter(
                user__email="creator@rerise.ai",
                reason="tariff",
                amount=1000,
            ).exists()
        )

    def test_scenarios_list(self):
        response = self.client.get("/api/v1/ibox/scenarios")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        self.assertEqual(data["token_balance"], 1000)
        self.assertEqual(len(data["scenarios"]), 10)

    def test_start_session_and_debit_tokens(self):
        scenario = Scenario.objects.get(slug="selling-post")
        response = self.client.post(
            "/api/v1/ibox/sessions",
            {
                "scenario_id": scenario.id,
                "message": "Пост про запуск AI-курса для партнёров",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data["data"]
        self.assertIn("session_id", data)
        self.assertEqual(data["message"]["role"], "assistant")
        self.assertEqual(data["message"]["tokens_used"], scenario.token_cost)
        self.assertEqual(data["token_balance"], 1000 - scenario.token_cost)

        session = ChatSession.objects.get(pk=data["session_id"])
        self.assertEqual(session.user.email, "creator@rerise.ai")
        self.assertEqual(session.messages.count(), 2)

    def test_continue_session(self):
        scenario = Scenario.objects.get(slug="selling-post")
        start = self.client.post(
            "/api/v1/ibox/sessions",
            {"scenario_id": scenario.id, "message": "Первый черновик"},
            format="json",
        )
        session_id = start.data["data"]["session_id"]

        follow = self.client.post(
            f"/api/v1/ibox/sessions/{session_id}/messages",
            {"message": "Сделай короче и добавь CTA"},
            format="json",
        )
        self.assertEqual(follow.status_code, status.HTTP_200_OK)
        self.assertEqual(ChatSession.objects.get(pk=session_id).messages.count(), 4)

        detail = self.client.get(f"/api/v1/ibox/sessions/{session_id}")
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(len(detail.data["data"]["messages"]), 4)

    def test_insufficient_tokens_returns_422(self):
        TokenBalance.objects.filter(user__email="creator@rerise.ai").update(available=0)
        scenario = Scenario.objects.get(slug="selling-post")
        response = self.client.post(
            "/api/v1/ibox/sessions",
            {"scenario_id": scenario.id, "message": "Нет токенов"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["error"]["code"], "INSUFFICIENT_TOKENS")

    def test_token_pack_purchase_credits(self):
        create = self.client.post(
            "/api/v1/store/orders",
            {"product_id": "tokens-1000", "order_type": "purchase"},
            format="json",
        )
        payment = Payment.objects.get(order_id=create.data["data"]["order_id"])
        PaymentConfirmationService.confirm(payment)

        user = User.objects.get(email="creator@rerise.ai")
        self.assertEqual(TokenService.get_available(user), 2000)

    def test_ai_provider_error_refunds_tokens(self):
        from unittest.mock import patch

        scenario = Scenario.objects.get(slug="selling-post")
        user = User.objects.get(email="creator@rerise.ai")
        before = TokenService.get_available(user)

        with patch("apps.ibox.services.get_ai_provider") as mock_get:
            mock_get.return_value.complete.side_effect = RuntimeError("API down")
            response = self.client.post(
                "/api/v1/ibox/sessions",
                {"scenario_id": scenario.id, "message": "Тест ошибки"},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(response.data["error"]["code"], "AI_PROVIDER_ERROR")
        self.assertEqual(TokenService.get_available(user), before)
        self.assertTrue(
            TokenTransaction.objects.filter(
                user=user, reason="refund", amount=scenario.token_cost
            ).exists()
        )
