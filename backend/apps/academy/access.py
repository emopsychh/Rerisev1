from django.conf import settings

from apps.academy.constants import TARIFF_ACADEMY_ACCESS
from apps.academy.models import Program
from apps.commerce.models import UserAccess
from apps.commerce.selectors import get_tariff_rank, get_user_subscription


def get_tariff_access_level(tariff_id: str | None) -> int:
    if not tariff_id:
        return 0
    return TARIFF_ACADEMY_ACCESS.get(tariff_id, get_tariff_rank(tariff_id))


def load_user_access_context(user) -> dict:
    """Один запрос subscription + один на product access для списка программ."""
    return {
        "subscription": get_user_subscription(user.pk),
        "product_access_ids": set(
            UserAccess.objects.filter(user=user, is_active=True).values_list(
                "product_id", flat=True
            )
        ),
    }


def user_has_program_access(
    user,
    program: Program,
    *,
    access_context: dict | None = None,
) -> bool:
    # Демо/локально: все опубликованные программы открыты без проверки тарифа.
    if getattr(settings, "ACADEMY_OPEN_ACCESS", False):
        return True

    if access_context is None:
        access_context = load_user_access_context(user)

    if program.required_product_id:
        return program.required_product_id in access_context["product_access_ids"]

    subscription = access_context["subscription"]
    if not program.required_tariff:
        return bool(subscription and subscription.is_active)

    if not subscription or not subscription.is_active:
        return False

    user_level = get_tariff_access_level(subscription.tariff_id)
    required_level = get_tariff_access_level(program.required_tariff)
    return user_level >= required_level
