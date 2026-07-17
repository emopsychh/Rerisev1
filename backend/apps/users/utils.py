import random
import string

from django.conf import settings
from django.db import models


def _generate_unique_value(model: type[models.Model], field: str, builder) -> str:
    while True:
        candidate = builder()
        if not model.objects.filter(**{field: candidate}).exists():
            return candidate


def generate_public_id() -> str:
    prefix = settings.RERISE_PUBLIC_ID_PREFIX

    def build():
        return f"{prefix}-{random.randint(1000, 9999)}"

    from .models import Profile

    return _generate_unique_value(Profile, "public_id", build)


def generate_referral_code() -> str:
    prefix = settings.RERISE_PUBLIC_ID_PREFIX

    def build():
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"{prefix}-{suffix}"

    from .models import ReferralCode

    return _generate_unique_value(ReferralCode, "code", build)
