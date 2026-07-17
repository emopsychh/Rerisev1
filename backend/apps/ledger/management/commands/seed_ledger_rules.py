from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.ledger.constants import DEFAULT_RULE_VERSION
from apps.ledger.models import RuleVersion

RULES_V1 = {
    "binary": {"collapsed_pv_per_usd": 10},
    "subscription": {
        "price_usd": 30,
        "sponsor_reward_usd": 9,
        "pv": 9,
    },
    "fast_start": {
        "window_days": 30,
        "required_partners": 4,
        "reward_usd": 90,
    },
    "withdrawal": {
        "min_usd": 100,
        "max_per_request_usd": 10000,
        "currency": "USDT",
    },
    "tariffs": {
        "rise": {
            "price_usd": 90,
            "personal_bonus_cap_usd": 30,
            "purchase_pv_cap": 30,
            "binary_depth": 3,
            "matching_lines": 1,
        },
        "rise-pro": {
            "price_usd": 300,
            "personal_bonus_cap_usd": 90,
            "purchase_pv_cap": 90,
            "binary_depth": 9,
            "matching_lines": 2,
        },
        "rise-pro-max": {
            "price_usd": 900,
            "personal_bonus_cap_usd": 300,
            "purchase_pv_cap": 300,
            "binary_depth": 15,
            "matching_lines": 3,
        },
    },
}


class Command(BaseCommand):
    help = "Seed ledger rule version v1.0"

    def handle(self, *args, **options):
        rule_version, created = RuleVersion.objects.get_or_create(
            version=DEFAULT_RULE_VERSION,
            defaults={
                "rules": RULES_V1,
                "effective_from": timezone.now(),
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created rule version {rule_version.version}"))
        else:
            rule_version.rules = RULES_V1
            rule_version.save(update_fields=["rules"])
            self.stdout.write(self.style.WARNING(f"Updated rules for {rule_version.version}"))
