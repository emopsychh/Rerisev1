from django.core.management.base import BaseCommand

from apps.partner.services import ActivityService


class Command(BaseCommand):
    help = "Деактивирует партнёров с истёкшей активностью и замораживает бинар."

    def handle(self, *args, **options):
        count = ActivityService.expire_due()
        self.stdout.write(self.style.SUCCESS(f"Деактивировано партнёров: {count}"))
