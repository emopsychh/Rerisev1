from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.serializers import (
    LoginSerializer,
    RefreshTokenSerializer,
    RegisterSerializer,
)
from apps.users.services import AuthenticationService, InvalidCredentialsError
from core.responses import error_response, success_response


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        data = AuthenticationService.build_token_response(user)
        return success_response(data, status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = AuthenticationService.authenticate(
                email=serializer.validated_data["email"],
                password=serializer.validated_data["password"],
            )
        except InvalidCredentialsError:
            return error_response(
                "UNAUTHORIZED",
                "Неверный email или пароль",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        return success_response(AuthenticationService.build_token_response(user))


class RefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refresh = RefreshToken(serializer.validated_data["refresh_token"])
        except (TokenError, InvalidToken):
            return error_response(
                "UNAUTHORIZED",
                "Недействительный refresh token",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        return success_response({"access_token": str(refresh.access_token)})
