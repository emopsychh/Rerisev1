from apps.users.models import User


def get_user_with_profile(user_id: int) -> User:
    return User.objects.select_related(
        "profile",
        "subscription",
        "partner_profile",
    ).get(pk=user_id)


def get_user_with_profile_and_settings(user_id: int) -> User:
    return User.objects.select_related(
        "profile",
        "notification_settings",
        "referral_code",
        "subscription",
        "partner_profile",
    ).get(pk=user_id)


def count_unread_notifications(user: User) -> int:
    return user.notifications.filter(is_read=False).count()
