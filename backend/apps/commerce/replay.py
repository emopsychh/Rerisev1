from django.core.cache import cache


WEBHOOK_REPLAY_TTL_SECONDS = 60 * 60 * 24  # 24h


def mark_webhook_seen(provider: str, external_id: str) -> bool:
    """
    Возвращает True, если событие новое (ещё не видели).
    False — повтор (replay).
    """
    key = f"webhook:seen:{provider}:{external_id}"
    # add() atomic: True only if key was absent
    return bool(cache.add(key, "1", timeout=WEBHOOK_REPLAY_TTL_SECONDS))
