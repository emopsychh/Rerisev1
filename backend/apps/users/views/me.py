from rest_framework import status
from rest_framework.views import APIView

from apps.commerce.presentation import subscription_payload_for_user
from apps.users.selectors import (
    count_unread_notifications,
    get_user_with_profile,
    get_user_with_profile_and_settings,
)
from apps.users.serializers import (
    InviteLinkSerializer,
    MeSerializer,
    MeSummarySerializer,
    ProfileReadSerializer,
    ProfileUpdateSerializer,
)
from apps.users.services import PhoneAlreadyExistsError, ProfileUpdateService, UserRegistrationService
from core.responses import error_response, success_response


class MeView(APIView):
    def get(self, request):
        user = get_user_with_profile(request.user.pk)
        user._unread_notifications = count_unread_notifications(user)
        return success_response(MeSerializer(user).data)


class MeSummaryView(APIView):
    def get(self, request):
        user = get_user_with_profile_and_settings(request.user.pk)
        data = {
            "subscription": subscription_payload_for_user(user, summary=True),
            "unread_notifications": count_unread_notifications(user),
            "referral_code": user.referral_code.code,
        }
        return success_response(MeSummarySerializer(data).data)


class MeProfileView(APIView):
    def get(self, request):
        user = get_user_with_profile_and_settings(request.user.pk)
        return success_response(ProfileReadSerializer(user.profile).data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        user = get_user_with_profile(request.user.pk)
        try:
            ProfileUpdateService.update(user, serializer.validated_data)
        except PhoneAlreadyExistsError as exc:
            return error_response(
                "VALIDATION_ERROR",
                str(exc),
                details={"phone": ["Уже занят"]},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user = get_user_with_profile_and_settings(user.pk)
        return success_response(ProfileReadSerializer(user.profile).data)


class InviteLinkView(APIView):
    def post(self, request):
        user = get_user_with_profile_and_settings(request.user.pk)
        data = {
            "referral_code": user.referral_code.code,
            "referral_url": UserRegistrationService.get_referral_url(user),
        }
        return success_response(InviteLinkSerializer(data).data)
