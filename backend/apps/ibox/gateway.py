from dataclasses import dataclass

from django.conf import settings

from apps.ibox.constants import PROVIDER_MOCK, PROVIDER_OPENAI


@dataclass
class AICompletionResult:
    content: str
    tokens_used: int
    model: str


class AIProvider:
    def complete(
        self,
        *,
        messages: list[dict],
        model: str,
        system_prompt: str | None = None,
    ) -> AICompletionResult:
        raise NotImplementedError


class MockAIProvider(AIProvider):
    """Детерминированный провайдер для тестов и dev без API-ключей."""

    def complete(
        self,
        *,
        messages: list[dict],
        model: str,
        system_prompt: str | None = None,
    ) -> AICompletionResult:
        last_user = ""
        for message in reversed(messages):
            if message.get("role") == "user":
                last_user = message.get("content", "")
                break

        preview = (last_user or "запрос").strip()
        if len(preview) > 120:
            preview = preview[:117] + "..."

        prefix = "Сценарий выполнен." if system_prompt else "Ответ AI Hub."
        content = (
            f"{prefix} (mock/{model})\n\n"
            f"Вот черновик по вашему запросу:\n«{preview}»\n\n"
            "Уточните тон, длину или CTA — доработаю."
        )
        # Грубая оценка токенов для каркаса
        tokens_used = max(8, len(content) // 4 + len(preview) // 4)
        return AICompletionResult(content=content, tokens_used=tokens_used, model=model)


class OpenAIProvider(AIProvider):
    """Минимальная обёртка OpenAI Chat Completions. Нужен OPENAI_API_KEY."""

    def complete(
        self,
        *,
        messages: list[dict],
        model: str,
        system_prompt: str | None = None,
    ) -> AICompletionResult:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "Пакет openai не установлен. Добавьте openai в requirements или используйте IBOX_AI_PROVIDER=mock."
            ) from exc

        api_key = getattr(settings, "OPENAI_API_KEY", "") or ""
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY не задан")

        payload = []
        if system_prompt:
            payload.append({"role": "system", "content": system_prompt})
        payload.extend(messages)

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(model=model, messages=payload)
        choice = response.choices[0].message
        usage = getattr(response, "usage", None)
        tokens_used = int(getattr(usage, "total_tokens", 0) or 0)
        if tokens_used <= 0:
            tokens_used = max(8, len(choice.content or "") // 4)

        return AICompletionResult(
            content=choice.content or "",
            tokens_used=tokens_used,
            model=model,
        )


def get_ai_provider() -> AIProvider:
    name = getattr(settings, "IBOX_AI_PROVIDER", PROVIDER_MOCK).lower()
    if name == PROVIDER_OPENAI:
        return OpenAIProvider()
    return MockAIProvider()
