from django.db import transaction

from apps.ibox.constants import DEFAULT_MODEL, ROLE_ASSISTANT, ROLE_SYSTEM, ROLE_USER
from apps.ibox.gateway import get_ai_provider
from apps.ibox.models import ChatMessage, ChatSession, Scenario
from apps.ibox.tokens import TokenService
from apps.users.models import User


class IboxAccessError(PermissionError):
    pass


class AIProviderError(Exception):
    """Ошибка внешнего AI-провайдера или его конфигурации."""


class ChatService:
    @staticmethod
    def start_session(
        user: User,
        *,
        message: str,
        scenario_id: int | None = None,
        model: str | None = None,
    ) -> dict:
        message = (message or "").strip()
        if not message:
            raise ValueError("Сообщение не может быть пустым")

        scenario = None
        system_prompt = None
        token_cost = 10

        if scenario_id is not None:
            scenario = Scenario.objects.filter(pk=scenario_id, is_active=True).first()
            if not scenario:
                raise LookupError("Сценарий не найден")
            system_prompt = scenario.prompt_template
            token_cost = scenario.token_cost
            model = model or scenario.default_model
        else:
            model = model or DEFAULT_MODEL

        # Короткая транзакция: резерв токенов + черновик сессии
        with transaction.atomic():
            session = ChatSession.objects.create(
                user=user,
                scenario=scenario,
                model=model,
                title=message[:80],
                tokens_spent=token_cost,
            )
            ChatMessage.objects.create(
                session=session,
                role=ROLE_USER,
                content=message,
                tokens_used=0,
            )
            TokenService.debit(user, token_cost, session=session)

        try:
            result = get_ai_provider().complete(
                messages=[{"role": ROLE_USER, "content": message}],
                model=model,
                system_prompt=system_prompt,
            )
        except Exception as exc:
            TokenService.refund(user, token_cost, session=session)
            ChatSession.objects.filter(pk=session.pk).update(tokens_spent=0)
            raise AIProviderError(str(exc)) from exc

        assistant = ChatMessage.objects.create(
            session=session,
            role=ROLE_ASSISTANT,
            content=result.content,
            tokens_used=result.tokens_used or token_cost,
        )

        return {
            "session_id": session.id,
            "message": {
                "role": assistant.role,
                "content": assistant.content,
                "tokens_used": token_cost,
            },
            "token_balance": TokenService.get_available(user),
        }

    @staticmethod
    def send_message(user: User, session_id: int, message: str) -> dict:
        message = (message or "").strip()
        if not message:
            raise ValueError("Сообщение не может быть пустым")

        with transaction.atomic():
            session = (
                ChatSession.objects.select_for_update()
                .filter(pk=session_id, user=user)
                .first()
            )
            if not session:
                raise LookupError("Сессия не найдена")

            scenario = session.scenario
            token_cost = scenario.token_cost if scenario else 10
            system_prompt = scenario.prompt_template if scenario else None
            model = session.model

            ChatMessage.objects.create(
                session=session,
                role=ROLE_USER,
                content=message,
                tokens_used=0,
            )
            TokenService.debit(user, token_cost, session=session)
            session.tokens_spent += token_cost
            session.save(update_fields=["tokens_spent", "updated_at"])

            history = list(
                ChatMessage.objects.filter(session=session)
                .exclude(role=ROLE_SYSTEM)
                .order_by("created_at")
                .values("role", "content")
            )

        try:
            result = get_ai_provider().complete(
                messages=history,
                model=model,
                system_prompt=system_prompt,
            )
        except Exception as exc:
            TokenService.refund(user, token_cost, session=session)
            with transaction.atomic():
                locked = ChatSession.objects.select_for_update().get(pk=session.pk)
                locked.tokens_spent = max(0, locked.tokens_spent - token_cost)
                locked.save(update_fields=["tokens_spent", "updated_at"])
            raise AIProviderError(str(exc)) from exc

        assistant = ChatMessage.objects.create(
            session=session,
            role=ROLE_ASSISTANT,
            content=result.content,
            tokens_used=result.tokens_used or token_cost,
        )

        return {
            "session_id": session.id,
            "message": {
                "role": assistant.role,
                "content": assistant.content,
                "tokens_used": token_cost,
            },
            "token_balance": TokenService.get_available(user),
        }
