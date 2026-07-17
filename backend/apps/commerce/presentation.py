from apps.commerce.models import Subscription
from apps.commerce.selectors import build_subscription_payload, get_user_subscription


def resolve_user_subscription(user) -> Subscription | None:
    try:
        return user.subscription
    except Subscription.DoesNotExist:
        return None


def subscription_payload_for_user(user, *, summary: bool = False) -> dict | None:
    subscription = resolve_user_subscription(user)
    if subscription is None:
        subscription = get_user_subscription(user.pk)
    return build_subscription_payload(subscription, summary=summary)
