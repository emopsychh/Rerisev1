from apps.ibox.models import ChatMessage, ChatSession, Scenario
from apps.ibox.tokens import TokenService


def serialize_scenario(scenario: Scenario) -> dict:
    return {
        "id": scenario.id,
        "slug": scenario.slug,
        "title": scenario.title,
        "category": scenario.category,
        "token_cost": scenario.token_cost,
        "description": scenario.description,
    }


def build_scenarios_payload(user, category: str | None = None) -> dict:
    qs = Scenario.objects.filter(is_active=True).order_by("sort_order", "title")
    if category:
        qs = qs.filter(category=category)

    recent = list(
        ChatSession.objects.filter(user=user)
        .exclude(title__isnull=True)
        .exclude(title="")
        .order_by("-created_at")
        .values_list("title", flat=True)[:5]
    )

    return {
        "token_balance": TokenService.get_available(user),
        "scenarios": [serialize_scenario(item) for item in qs],
        "recent_tasks": recent,
    }


def serialize_session_brief(session: ChatSession) -> dict:
    return {
        "id": session.id,
        "title": session.title,
        "scenario_id": session.scenario_id,
        "model": session.model,
        "tokens_spent": session.tokens_spent,
        "created_at": session.created_at.isoformat().replace("+00:00", "Z"),
    }


def serialize_message(message: ChatMessage) -> dict:
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "tokens_used": message.tokens_used,
        "created_at": message.created_at.isoformat().replace("+00:00", "Z"),
    }


def serialize_session_detail(session: ChatSession) -> dict:
    messages = [
        serialize_message(message)
        for message in session.messages.order_by("created_at")
    ]
    return {
        **serialize_session_brief(session),
        "messages": messages,
    }


def get_user_sessions_queryset(user):
    return ChatSession.objects.filter(user=user).select_related("scenario")


def get_user_session(user, session_id: int) -> ChatSession | None:
    return (
        ChatSession.objects.filter(pk=session_id, user=user)
        .select_related("scenario")
        .prefetch_related("messages")
        .first()
    )
