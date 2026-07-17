from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import NotificationSettings, Profile, ReferralCode, User
from apps.users.utils import generate_public_id, generate_referral_code


class ReferralCodeError(ValueError):
    pass


class PhoneAlreadyExistsError(ValueError):
    pass


class InvalidCredentialsError(ValueError):
    pass


class UserRegistrationService:
    @staticmethod
    @transaction.atomic
    def register(
        *,
        email: str,
        password: str,
        phone: str | None = None,
        first_name: str = "",
        last_name: str = "",
        referral_code: str | None = None,
    ) -> User:
        inviter = (
            UserRegistrationService._resolve_inviter(referral_code)
            if referral_code
            else None
        )

        user = User.objects.create_user(
            email=email,
            password=password,
            phone=phone or None,
            invited_by=inviter,
        )
        Profile.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            public_id=generate_public_id(),
        )
        ReferralCode.objects.create(user=user, code=generate_referral_code())
        NotificationSettings.objects.create(user=user)
        return user

    @staticmethod
    def _resolve_inviter(referral_code: str) -> User:
        try:
            code = ReferralCode.objects.select_related("user").get(
                code=referral_code,
                is_active=True,
            )
        except ReferralCode.DoesNotExist as exc:
            raise ReferralCodeError("Неверный реферальный код") from exc
        return code.user

    @staticmethod
    def get_referral_url(user: User) -> str:
        base = settings.RERISE_REFERRAL_BASE_URL.rstrip("/")
        return f"{base}/{user.referral_code.code}"


class AuthenticationService:
    @staticmethod
    def authenticate(email: str, password: str) -> User:
        try:
            user = User.objects.select_related("profile").get(email=email.lower())
        except User.DoesNotExist as exc:
            raise InvalidCredentialsError from exc

        if not user.check_password(password):
            raise InvalidCredentialsError

        if not user.is_active:
            raise InvalidCredentialsError

        user.last_login_at = timezone.now()
        user.save(update_fields=["last_login_at"])
        return user

    @staticmethod
    def build_token_response(user: User) -> dict:
        refresh = RefreshToken.for_user(user)
        return {
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "public_id": user.profile.public_id,
            },
        }


class ProfileUpdateService:
    PROFILE_FIELDS = ("first_name", "last_name", "country", "city", "language")

    @staticmethod
    @transaction.atomic
    def update(user: User, data: dict) -> User:
        if "phone" in data:
            phone = data["phone"] or None
            if phone and User.objects.exclude(pk=user.pk).filter(phone=phone).exists():
                raise PhoneAlreadyExistsError(
                    "Пользователь с таким телефоном уже существует"
                )
            user.phone = phone
            user.save(update_fields=["phone", "updated_at"])

        profile_updates = {
            key: data[key] for key in ProfileUpdateService.PROFILE_FIELDS if key in data
        }
        if profile_updates:
            profile = user.profile
            for key, value in profile_updates.items():
                setattr(profile, key, value)
            profile.save()

        return user
