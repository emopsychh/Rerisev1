from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.services import UserRegistrationService


class UsersAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.inviter = UserRegistrationService.register(
            email="inviter@rerise.ai",
            password="password123",
            first_name="Иван",
            last_name="Партнёр",
        )
        self.inviter.referral_code.code = "RERISE-INV1"
        self.inviter.referral_code.save(update_fields=["code"])

    def _register(self, email: str, **extra):
        payload = {"email": email, "password": "password123", **extra}
        return self.client.post("/api/v1/auth/register", payload, format="json")

    def _auth_headers(self, email: str):
        response = self.client.post(
            "/api/v1/auth/login",
            {"email": email, "password": "password123"},
            format="json",
        )
        token = response.data["data"]["access_token"]
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def test_register_with_referral_and_login(self):
        response = self._register(
            "user@rerise.ai",
            first_name="Александр",
            last_name="Левес",
            referral_code="RERISE-INV1",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access_token", response.data["data"])

        user = self.inviter.invitees.get(email="user@rerise.ai")
        self.assertEqual(user.invited_by_id, self.inviter.id)
        self.assertTrue(user.profile.public_id.startswith("RERISE-"))

        login = self.client.post(
            "/api/v1/auth/login",
            {"email": "user@rerise.ai", "password": "password123"},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)

    def test_register_rejects_invalid_referral_code(self):
        response = self._register(
            "bad-ref@rerise.ai",
            referral_code="RERISE-UNKNOWN",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_rejects_invalid_credentials(self):
        response = self.client.post(
            "/api/v1/auth/login",
            {"email": "missing@rerise.ai", "password": "wrong"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_requires_auth(self):
        response = self.client.get("/api/v1/me")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_update(self):
        self._register("profile@rerise.ai")
        self.client.credentials(**self._auth_headers("profile@rerise.ai"))

        response = self.client.patch(
            "/api/v1/me/profile",
            {"city": "Москва", "country": "Россия"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["city"], "Москва")

    def test_invite_link(self):
        self._register("invite@rerise.ai")
        self.client.credentials(**self._auth_headers("invite@rerise.ai"))

        response = self.client.post("/api/v1/me/invite-link", format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("referral_url", response.data["data"])
