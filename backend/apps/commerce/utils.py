from datetime import timedelta

from django.conf import settings

from apps.commerce.constants import ACTIVITY_DAYS_PER_MONTH


def activity_duration(months: int = 1) -> timedelta:
    days = getattr(settings, "ACTIVITY_DAYS_PER_MONTH", ACTIVITY_DAYS_PER_MONTH)
    return timedelta(days=days * months)
