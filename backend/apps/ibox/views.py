from rest_framework import status
from rest_framework.views import APIView

from apps.ibox.selectors import (
    build_scenarios_payload,
    get_user_session,
    get_user_sessions_queryset,
    serialize_session_brief,
    serialize_session_detail,
)
from apps.ibox.serializers import SendMessageSerializer, StartSessionSerializer
from apps.ibox.services import AIProviderError, ChatService
from apps.ibox.tokens import InsufficientTokensError
from core.pagination import StandardPagination
from core.responses import error_response, success_response


def _handle_chat_errors(exc):
    if isinstance(exc, LookupError):
        return error_response(
            "NOT_FOUND",
            str(exc),
            status_code=status.HTTP_404_NOT_FOUND,
        )
    if isinstance(exc, InsufficientTokensError):
        return error_response(
            "INSUFFICIENT_TOKENS",
            str(exc),
            details={"available": exc.available, "required": exc.required},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    if isinstance(exc, AIProviderError):
        return error_response(
            "AI_PROVIDER_ERROR",
            "Сервис генерации временно недоступен",
            details={"detail": str(exc)},
            status_code=status.HTTP_502_BAD_GATEWAY,
        )
    if isinstance(exc, ValueError):
        return error_response("VALIDATION_ERROR", str(exc))
    raise exc


class ScenarioListView(APIView):
    def get(self, request):
        category = request.query_params.get("category")
        return success_response(build_scenarios_payload(request.user, category))


class SessionListCreateView(APIView):
    pagination_class = StandardPagination

    def get(self, request):
        queryset = get_user_sessions_queryset(request.user)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        data = [serialize_session_brief(session) for session in page]
        return paginator.get_paginated_response(data)

    def post(self, request):
        serializer = StartSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            result = ChatService.start_session(
                request.user,
                message=data["message"],
                scenario_id=data.get("scenario_id"),
                model=data.get("model") or None,
            )
        except Exception as exc:
            return _handle_chat_errors(exc)

        return success_response(result, status_code=status.HTTP_201_CREATED)


class SessionDetailView(APIView):
    def get(self, request, session_id: int):
        session = get_user_session(request.user, session_id)
        if not session:
            return error_response(
                "NOT_FOUND",
                "Сессия не найдена",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return success_response(serialize_session_detail(session))


class SessionMessageView(APIView):
    def post(self, request, session_id: int):
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = ChatService.send_message(
                request.user,
                session_id,
                serializer.validated_data["message"],
            )
        except Exception as exc:
            return _handle_chat_errors(exc)

        return success_response(result)
