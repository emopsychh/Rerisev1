from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.commerce.constants import (
    MATCHING_PERCENT,
    QUICK_START_LABEL,
    RENEWAL_WINDOW_DAYS,
    TARIFF_RANK_FALLBACK,
)
from apps.commerce.models import Order, Product, Subscription, TariffPlan
from apps.commerce.utils import activity_duration


def get_active_tariff_products():
    return (
        Product.objects.filter(type=Product.TYPE_TARIFF, is_active=True)
        .select_related("tariff_plan")
        .order_by("price_usd")
    )


def get_token_products():
    return Product.objects.filter(type=Product.TYPE_TOKENS, is_active=True).order_by(
        "price_usd"
    )


def get_user_subscription(user_id: int) -> Subscription | None:
    return Subscription.objects.filter(user_id=user_id).first()


def subscription_can_renew(subscription: Subscription | None) -> bool:
    """True если активность истекла или входит в окно продления."""
    if not subscription:
        return False
    window_days = getattr(settings, "RENEWAL_WINDOW_DAYS", RENEWAL_WINDOW_DAYS)
    return subscription.active_until <= timezone.now() + timedelta(days=window_days)


def get_order_for_user(order_id: int, user_id: int) -> Order:
    return (
        Order.objects.select_related("product", "product__tariff_plan")
        .prefetch_related("payments")
        .get(pk=order_id, user_id=user_id)
    )


def get_tariff_rank(tariff_id: str) -> int:
    rank = (
        TariffPlan.objects.filter(tariff_id=tariff_id)
        .values_list("purchase_pv_cap", flat=True)
        .first()
    )
    if rank is not None:
        return rank
    return TARIFF_RANK_FALLBACK.get(tariff_id, 0)


def get_tariff_caps(tariff_id: str) -> dict | None:
    plan = TariffPlan.objects.filter(tariff_id=tariff_id).first()
    if not plan:
        return None
    return {
        "bonus_usd": plan.personal_bonus_cap_usd,
        "pv": plan.purchase_pv_cap,
        "binary_depth": plan.binary_depth,
        "matching_lines": plan.matching_lines,
        "quick_start_eligible": plan.quick_start_eligible,
    }


def get_tariff_display_name(tariff_id: str) -> str:
    name = (
        Product.objects.filter(slug=tariff_id, type=Product.TYPE_TARIFF)
        .values_list("name", flat=True)
        .first()
    )
    return name or tariff_id


def serialize_tariff_product(product: Product) -> dict:
    plan: TariffPlan = product.tariff_plan
    data = {
        "id": plan.tariff_id,
        "name": product.name,
        "price_usd": float(product.price_usd),
        "description": product.description,
        "terms": {
            "personal_bonus_cap_usd": float(plan.personal_bonus_cap_usd),
            "purchase_pv_cap": plan.purchase_pv_cap,
            "binary_depth": plan.binary_depth,
            "matching_lines": plan.matching_lines,
            "matching_percent": MATCHING_PERCENT,
        },
        "quick_start_eligible": plan.quick_start_eligible,
    }
    if plan.quick_start_eligible:
        data["quick_start"] = product.metadata.get("quick_start", QUICK_START_LABEL)
    if product.description:
        data["included"] = [product.description]
    return data


def serialize_token_store(balance: int = 0) -> dict:
    packs = get_token_products()
    return {
        "balance": balance,
        "packs": [
            {
                "id": pack.slug,
                "amount": pack.metadata.get("amount", 0),
                "price_usd": float(pack.price_usd),
            }
            for pack in packs
        ],
    }


def serialize_create_order_response(order: Order) -> dict:
    payment = order.payments.latest("created_at")
    return {
        "order_id": order.id,
        "product_name": order.product.name,
        "amount_usd": float(order.amount_usd),
        "status": order.status,
        "payment": {
            "provider": payment.provider,
            "payment_url": payment.payment_url,
            "instructions": payment.instructions,
            "expires_at": payment.expires_at,
        },
    }


def serialize_order_detail(order: Order) -> dict:
    data = {
        "order_id": order.id,
        "status": order.status,
        "paid_at": order.paid_at,
        "granted_access": None,
    }

    if order.status != Order.STATUS_PAID:
        return data

    subscription = get_user_subscription(order.user_id)
    granted_access = {
        "tariff": subscription.tariff_id if subscription else None,
        "activity_until": subscription.active_until if subscription else None,
        "tokens_credited": 0,
    }

    if order.product.type == Product.TYPE_TARIFF:
        try:
            granted_access["tokens_credited"] = order.product.tariff_plan.initial_tokens
        except TariffPlan.DoesNotExist:
            pass
    elif order.product.type == Product.TYPE_TOKENS:
        granted_access["tariff"] = None
        granted_access["activity_until"] = None
        granted_access["tokens_credited"] = int(
            (order.product.metadata or {}).get("amount") or 0
        )

    data["granted_access"] = granted_access
    return data


def build_subscription_payload(
    subscription: Subscription | None,
    *,
    summary: bool = False,
) -> dict | None:
    if not subscription:
        return None

    tariff_name = get_tariff_display_name(subscription.tariff_id)
    can_renew = subscription_can_renew(subscription)

    if summary:
        return {
            "tariff_name": tariff_name,
            "activity_until": subscription.active_until,
            "can_renew": can_renew,
        }

    return {
        "tariff_id": subscription.tariff_id,
        "tariff_name": tariff_name,
        "is_active": subscription.is_active,
        "activity_until": subscription.active_until,
    }
