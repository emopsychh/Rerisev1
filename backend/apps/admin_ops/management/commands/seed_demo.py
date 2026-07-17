from django.core.management.base import BaseCommand
from django.core.management import call_command


SEED_COMMANDS = [
    "seed_commerce",
    "seed_ledger_rules",
    "seed_academy",
    "seed_content",
    "seed_ibox",
    "seed_crm",
]


class Command(BaseCommand):
    help = "Seed full demo environment (all domain seeds)"

    def handle(self, *args, **options):
        for name in SEED_COMMANDS:
            self.stdout.write(f"- {name}")
            call_command(name)
        self.stdout.write(self.style.SUCCESS("Demo seed complete"))
