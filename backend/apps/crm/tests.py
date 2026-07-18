from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.commerce.models import Order
from apps.crm.models import Lead, LeadActivity
from tests.support import AuthStoreTestMixin


class CrmAPITestCase(AuthStoreTestMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.seed_store()
        call_command("seed_crm")
        self.register_user("crm@rerise.ai", first_name="CRM", last_name="Тест")
        self.login_user("crm@rerise.ai")
        self.buy_tariff("rise")

    def test_kanban_empty_stages(self):
        response = self.client.get("/api/v1/crm/leads")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stages = response.data["data"]["stages"]
        self.assertEqual(len(stages), 4)
        self.assertEqual([s["slug"] for s in stages], ["new", "contact", "meeting", "deal"])

    def test_create_update_move_delete_lead(self):
        create = self.client.post(
            "/api/v1/crm/leads",
            {
                "name": "Марина К.",
                "source": "Instagram",
                "phone": "+79002145511",
                "contact": "@marina.ai",
                "stage": "new",
                "task": "Созвон завтра",
                "value_usd": "300.00",
                "note": "Интересуется AI Hub",
            },
            format="json",
        )
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)
        lead_id = create.data["data"]["id"]
        self.assertEqual(create.data["data"]["stage"], "new")

        patch = self.client.patch(
            f"/api/v1/crm/leads/{lead_id}",
            {"stage": "contact", "task": "Отправить презентацию"},
            format="json",
        )
        self.assertEqual(patch.status_code, status.HTTP_200_OK)
        self.assertEqual(patch.data["data"]["stage"], "contact")

        actions = list(
            LeadActivity.objects.filter(lead_id=lead_id)
            .order_by("id")
            .values_list("action", flat=True)
        )
        self.assertIn("created", actions)
        self.assertIn("stage_changed", actions)
        self.assertIn("updated", actions)

        kanban = self.client.get("/api/v1/crm/leads")
        by_slug = {s["slug"]: s for s in kanban.data["data"]["stages"]}
        self.assertEqual(len(by_slug["contact"]["leads"]), 1)
        self.assertEqual(len(by_slug["new"]["leads"]), 0)

        delete = self.client.delete(f"/api/v1/crm/leads/{lead_id}")
        self.assertEqual(delete.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Lead.objects.filter(pk=lead_id).exists())

    def test_cannot_access_other_user_lead(self):
        other = APIClient()
        other.post(
            "/api/v1/auth/register",
            {"email": "other2@rerise.ai", "password": "password123"},
            format="json",
        )
        login = other.post(
            "/api/v1/auth/login",
            {"email": "other2@rerise.ai", "password": "password123"},
            format="json",
        )
        other.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['data']['access_token']}")
        created = other.post(
            "/api/v1/crm/leads",
            {"name": "Чужой лид", "stage": "new"},
            format="json",
        )
        other_id = created.data["data"]["id"]

        response = self.client.get("/api/v1/crm/leads")
        all_ids = [
            lead["id"]
            for stage in response.data["data"]["stages"]
            for lead in stage["leads"]
        ]
        self.assertNotIn(other_id, all_ids)

        forbidden = self.client.patch(
            f"/api/v1/crm/leads/{other_id}",
            {"stage": "deal"},
            format="json",
        )
        self.assertEqual(forbidden.status_code, status.HTTP_404_NOT_FOUND)


class PartnerRenewHomeTestCase(AuthStoreTestMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.seed_store()
        call_command("seed_academy")
        call_command("seed_content")
        call_command("seed_crm")
        self.register_user("home@rerise.ai", first_name="Home", last_name="Тест")
        self.login_user("home@rerise.ai")
        self.buy_tariff("rise")

    def test_partner_renew_creates_order(self):
        from apps.commerce.models import Subscription

        subscription = Subscription.objects.get(user__email="home@rerise.ai")
        subscription.active_until = timezone.now() + timedelta(days=3)
        subscription.save(update_fields=["active_until", "updated_at"])

        response = self.client.post("/api/v1/partner/renew")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("order_id", response.data["data"])
        self.assertEqual(response.data["data"]["amount_usd"], 30.0)
        order = Order.objects.get(pk=response.data["data"]["order_id"])
        self.assertEqual(order.order_type, "renewal")
        self.assertEqual(order.product.slug, "subscription")

    def test_partner_renew_blocked_outside_window(self):
        response = self.client.post("/api/v1/partner/renew")
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data["error"]["code"], "BUSINESS_RULE_ERROR")

    def test_home_includes_next_action_and_partner(self):
        response = self.client.get("/api/v1/home")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        self.assertIn("banners", data)
        self.assertIn("next_action", data)
        self.assertIn("partner_summary", data)
        self.assertEqual(data["partner_summary"]["tariff_id"], "rise")
        self.assertGreaterEqual(data["token_balance"], 0)
        self.assertTrue(data["ai_box_widget"]["is_available"])

    def test_dashboard_has_can_renew(self):
        response = self.client.get("/api/v1/partner/dashboard")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("can_renew", response.data["data"])
        self.assertTrue(response.data["data"]["is_partner"])
