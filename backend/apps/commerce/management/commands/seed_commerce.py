from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.commerce.constants import QUICK_START_LABEL
from apps.commerce.models import Product, TariffPlan


TARIFFS = [
    {
        "slug": "rise",
        "name": "Rise",
        "price_usd": Decimal("90.00"),
        "description": "Партнёрский тариф с физической PV-глубиной 3 уровня",
        "tariff_id": "rise",
        "personal_bonus_cap_usd": Decimal("30.00"),
        "purchase_pv_cap": 30,
        "binary_depth": 3,
        "matching_lines": 1,
        "quick_start_eligible": False,
        "initial_tokens": 1000,
    },
    {
        "slug": "rise-pro",
        "name": "Rise Pro",
        "price_usd": Decimal("300.00"),
        "description": "Расширенный партнёрский тариф",
        "tariff_id": "rise-pro",
        "personal_bonus_cap_usd": Decimal("90.00"),
        "purchase_pv_cap": 90,
        "binary_depth": 9,
        "matching_lines": 2,
        "quick_start_eligible": True,
        "initial_tokens": 5000,
    },
    {
        "slug": "rise-pro-max",
        "name": "Rise Pro Max",
        "price_usd": Decimal("900.00"),
        "description": "Максимальный партнёрский тариф",
        "tariff_id": "rise-pro-max",
        "personal_bonus_cap_usd": Decimal("300.00"),
        "purchase_pv_cap": 300,
        "binary_depth": 15,
        "matching_lines": 3,
        "quick_start_eligible": True,
        "initial_tokens": 15000,
    },
]

TOKEN_PACKS = [
    {
        "slug": "tokens-1000",
        "name": "1000 токенов",
        "price_usd": Decimal("10.00"),
        "amount": 1000,
    },
    {
        "slug": "tokens-5000",
        "name": "5000 токенов",
        "price_usd": Decimal("40.00"),
        "amount": 5000,
    },
]


class Command(BaseCommand):
    help = "Seed commerce products: tariffs, subscription, token packs"

    def handle(self, *args, **options):
        for item in TARIFFS:
            product, _ = Product.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "type": Product.TYPE_TARIFF,
                    "name": item["name"],
                    "description": item["description"],
                    "price_usd": item["price_usd"],
                    "is_active": True,
                    "metadata": (
                        {"quick_start": QUICK_START_LABEL}
                        if item["quick_start_eligible"]
                        else {}
                    ),
                },
            )
            TariffPlan.objects.update_or_create(
                product=product,
                defaults={
                    "tariff_id": item["tariff_id"],
                    "included_months": 1,
                    "personal_bonus_cap_usd": item["personal_bonus_cap_usd"],
                    "purchase_pv_cap": item["purchase_pv_cap"],
                    "binary_depth": item["binary_depth"],
                    "matching_lines": item["matching_lines"],
                    "quick_start_eligible": item["quick_start_eligible"],
                    "initial_tokens": item["initial_tokens"],
                },
            )
            self.stdout.write(f"Tariff: {item['slug']}")

        Product.objects.update_or_create(
            slug="subscription",
            defaults={
                "type": Product.TYPE_SUBSCRIPTION,
                "name": "Продление активности",
                "description": "Ежемесячное продление партнёрской активности",
                "price_usd": Decimal("30.00"),
                "is_active": True,
                "metadata": {"months": 1},
            },
        )
        self.stdout.write("Subscription: subscription")

        for pack in TOKEN_PACKS:
            Product.objects.update_or_create(
                slug=pack["slug"],
                defaults={
                    "type": Product.TYPE_TOKENS,
                    "name": pack["name"],
                    "price_usd": pack["price_usd"],
                    "is_active": True,
                    "metadata": {"amount": pack["amount"]},
                },
            )
            self.stdout.write(f"Tokens: {pack['slug']}")

        self.stdout.write(self.style.SUCCESS("Commerce seed complete."))
