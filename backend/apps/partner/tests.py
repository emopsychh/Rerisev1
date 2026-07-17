from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.partner.models import BinaryPlacement, PartnerProfile, SponsorLink
from tests.support import AuthStoreTestMixin


class PartnerAPITestCase(AuthStoreTestMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.seed_store()

    def test_three_user_chain_with_binary_placement(self):
        self.register_user("alpha@rerise.ai", first_name="Альфа", last_name="Партнёр")
        self.login_user("alpha@rerise.ai")
        self.buy_tariff("rise")

        alpha = PartnerProfile.objects.get(user__email="alpha@rerise.ai")
        alpha_placement = BinaryPlacement.objects.get(partner=alpha)
        self.assertEqual(alpha_placement.depth, 0)
        self.assertIsNone(alpha_placement.parent_id)
        referral_code = alpha.user.referral_code.code

        self.client.credentials()
        self.register_user(
            "beta@rerise.ai",
            first_name="Бета",
            last_name="Партнёр",
            referral_code=referral_code,
        )
        self.login_user("beta@rerise.ai")
        self.buy_tariff("rise")

        beta = PartnerProfile.objects.get(user__email="beta@rerise.ai")
        beta_placement = BinaryPlacement.objects.get(partner=beta)
        self.assertEqual(beta_placement.parent_id, alpha.id)
        self.assertEqual(beta_placement.leg, alpha_placement.leg)
        self.assertEqual(beta_placement.depth, 1)
        self.assertTrue(SponsorLink.objects.filter(partner=beta, sponsor=alpha).exists())

        beta_user = beta.user
        self.client.credentials()
        self.register_user(
            "gamma@rerise.ai",
            first_name="Гамма",
            last_name="Партнёр",
            referral_code=beta_user.referral_code.code,
        )
        self.login_user("gamma@rerise.ai")
        self.buy_tariff("rise-pro")

        gamma = PartnerProfile.objects.get(user__email="gamma@rerise.ai")
        gamma_placement = BinaryPlacement.objects.get(partner=gamma)
        self.assertEqual(gamma_placement.parent_id, beta.id)
        self.assertEqual(gamma_placement.depth, 2)
        self.assertTrue(SponsorLink.objects.filter(partner=gamma, sponsor=beta).exists())

    def test_partner_invited_list(self):
        self.register_user("sponsor@rerise.ai", first_name="Спонсор", last_name="Один")
        self.login_user("sponsor@rerise.ai")
        self.buy_tariff("rise-pro")
        sponsor = PartnerProfile.objects.get(user__email="sponsor@rerise.ai")
        code = sponsor.user.referral_code.code

        self.client.credentials()
        self.register_user(
            "invitee@rerise.ai",
            first_name="Мария",
            last_name="Козлова",
            referral_code=code,
        )
        self.login_user("invitee@rerise.ai")
        self.buy_tariff("rise")

        self.login_user("sponsor@rerise.ai")
        response = self.client.get("/api/v1/partner/invited")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invited = response.data["data"]
        self.assertEqual(len(invited), 1)
        self.assertEqual(invited[0]["name"], "Мария К.")
        self.assertEqual(invited[0]["tariff"], "Rise")
        self.assertTrue(invited[0]["is_active"])

    def test_me_and_profile_partner_fields(self):
        self.register_user("partner@rerise.ai", first_name="Алекс", last_name="Тестов")
        self.login_user("partner@rerise.ai")
        self.buy_tariff("rise-pro")

        me = self.client.get("/api/v1/me")
        self.assertTrue(me.data["data"]["is_partner"])
        self.assertEqual(me.data["data"]["subscription"]["tariff_id"], "rise-pro")

        profile = self.client.get("/api/v1/me/profile")
        partner = profile.data["data"]["partner"]
        self.assertIsNotNone(partner)
        self.assertEqual(partner["tariff_name"], "Rise Pro")
        self.assertTrue(partner["is_active"])
        self.assertEqual(partner["historical_rank"], "Партнёр I")

    def test_non_partner_invited_returns_empty(self):
        self.register_user("guest@rerise.ai")
        self.login_user("guest@rerise.ai")
        response = self.client.get("/api/v1/partner/invited")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"], [])
