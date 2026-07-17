from rest_framework import serializers

from apps.commerce.presentation import subscription_payload_for_user
from apps.partner.presentation import partner_payload_for_user
from apps.partner.selectors import user_is_partner
from apps.users.models import Notification, NotificationSettings, Profile, User
from apps.users.services import (
    PhoneAlreadyExistsError,
    ReferralCodeError,
    UserRegistrationService,
)


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone = serializers.CharField(required=False, allow_blank=True, max_length=20)
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=100)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=100)
    referral_code = serializers.CharField(required=False, allow_blank=True, max_length=32)

    def validate_email(self, value: str) -> str:
        email = value.lower()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует")
        return email

    def validate_phone(self, value: str) -> str:
        if not value:
            return ""
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Пользователь с таким телефоном уже существует")
        return value

    def create(self, validated_data: dict) -> User:
        referral_code = validated_data.pop("referral_code", "").strip() or None
        try:
            return UserRegistrationService.register(
                referral_code=referral_code,
                **validated_data,
            )
        except ReferralCodeError as exc:
            raise serializers.ValidationError({"referral_code": [str(exc)]}) from exc


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value: str) -> str:
        return value.lower()


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class NotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSettings
        fields = ("email_enabled", "push_enabled")


class MeSerializer(serializers.ModelSerializer):
    public_id = serializers.CharField(source="profile.public_id", read_only=True)
    first_name = serializers.CharField(source="profile.first_name", read_only=True)
    last_name = serializers.CharField(source="profile.last_name", read_only=True)
    avatar_url = serializers.URLField(source="profile.avatar_url", read_only=True)
    language = serializers.CharField(source="profile.language", read_only=True)
    is_partner = serializers.SerializerMethodField()
    subscription = serializers.SerializerMethodField()
    unread_notifications = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "phone",
            "public_id",
            "first_name",
            "last_name",
            "avatar_url",
            "language",
            "is_partner",
            "subscription",
            "unread_notifications",
        )

    def get_is_partner(self, obj: User) -> bool:
        return user_is_partner(obj)

    def get_subscription(self, obj: User):
        return subscription_payload_for_user(obj)

    def get_unread_notifications(self, obj: User) -> int:
        if hasattr(obj, "_unread_notifications"):
            return obj._unread_notifications
        return obj.notifications.filter(is_read=False).count()


class MeSummarySerializer(serializers.Serializer):
    subscription = serializers.JSONField(allow_null=True)
    unread_notifications = serializers.IntegerField()
    referral_code = serializers.CharField()


class ProfileReadSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True, allow_null=True)
    avatar_url = serializers.URLField(allow_blank=True, required=False)
    partner = serializers.SerializerMethodField()
    notifications = NotificationSettingsSerializer(
        source="user.notification_settings",
        read_only=True,
    )

    class Meta:
        model = Profile
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone",
            "country",
            "city",
            "language",
            "avatar_url",
            "public_id",
            "partner",
            "notifications",
        )

    def get_partner(self, obj: Profile):
        return partner_payload_for_user(obj.user)

    def to_representation(self, instance: Profile) -> dict:
        data = super().to_representation(instance)
        if not data.get("avatar_url"):
            data["avatar_url"] = None
        return data


class ProfileUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=100)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=100)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=20)
    country = serializers.CharField(required=False, allow_blank=True, max_length=100)
    city = serializers.CharField(required=False, allow_blank=True, max_length=100)
    language = serializers.ChoiceField(required=False, choices=Profile.LANGUAGE_CHOICES)


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ("id", "type", "title", "body", "is_read", "created_at")


class InviteLinkSerializer(serializers.Serializer):
    referral_code = serializers.CharField()
    referral_url = serializers.URLField()
