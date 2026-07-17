from django.core.management.base import BaseCommand

from apps.crm.models import LeadStage

STAGES = [
    {"slug": "new", "name": "Новые", "color": "blue", "sort_order": 0},
    {"slug": "contact", "name": "Контакты", "color": "green", "sort_order": 1},
    {"slug": "meeting", "name": "Встречи", "color": "orange", "sort_order": 2},
    {"slug": "deal", "name": "Сделки", "color": "violet", "sort_order": 3},
]


class Command(BaseCommand):
    help = "Seed CRM lead stages (4 columns)"

    def handle(self, *args, **options):
        for item in STAGES:
            stage, created = LeadStage.objects.update_or_create(
                slug=item["slug"],
                defaults=item,
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"{action} stage: {stage.slug}")

        self.stdout.write(self.style.SUCCESS(f"CRM seed complete: {LeadStage.objects.count()} stages"))
