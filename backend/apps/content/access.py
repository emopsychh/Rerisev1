from urllib.parse import urlparse

from apps.academy.access import get_tariff_access_level, load_user_access_context
from apps.content.constants import CHAT_TYPE_OPEN, CHAT_TYPE_SERVICE, TARIFF_MATERIAL_ACCESS
from apps.content.models import MaterialGroup, TelegramChat
from apps.partner.engine_constants import rank_index, rank_name
from apps.partner.models import PartnerProfile


def resolve_material_tariff_level(tariff_id: str | None) -> int | None:
    """Уровень тарифа для материалов. None = неизвестный id → deny."""
    if not tariff_id:
        return None
    if tariff_id in TARIFF_MATERIAL_ACCESS:
        return TARIFF_MATERIAL_ACCESS[tariff_id]
    level = get_tariff_access_level(tariff_id)
    if level > 0:
        return level
    return None


def user_has_material_group_access(
    user,
    group: MaterialGroup,
    *,
    access_context: dict | None = None,
) -> bool:
    if not group.required_tariff:
        return True

    required_level = resolve_material_tariff_level(group.required_tariff)
    if required_level is None:
        return False

    if access_context is None:
        access_context = load_user_access_context(user)

    subscription = access_context["subscription"]
    if not subscription or not subscription.is_active:
        return False

    user_level = resolve_material_tariff_level(subscription.tariff_id) or 0
    return user_level >= required_level


def user_has_chat_access(
    user,
    chat: TelegramChat,
    *,
    partner: PartnerProfile | None = None,
) -> bool:
    if chat.chat_type in (CHAT_TYPE_OPEN, CHAT_TYPE_SERVICE):
        return True
    if not chat.min_rank:
        return True

    if partner is None:
        partner = PartnerProfile.objects.filter(user=user).first()
    if not partner:
        return False

    return rank_index(partner.highest_rank) >= rank_index(chat.min_rank)


def chat_access_requirement_text(chat: TelegramChat) -> str | None:
    if chat.access_requirement:
        return chat.access_requirement
    if chat.min_rank:
        return f"{rank_name(chat.min_rank)} и выше"
    return None


def is_safe_download_redirect(url: str | None) -> bool:
    """Только site-relative пути (/media/...), без open redirect."""
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    if not url.startswith("/") or url.startswith("//"):
        return False
    parsed = urlparse(url)
    if parsed.scheme or parsed.netloc:
        return False
    return True
