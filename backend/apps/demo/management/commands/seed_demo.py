import json

from django.core.management.base import BaseCommand

from apps.demo.seed import seed_demo


class Command(BaseCommand):
    help = "Seed the database with synthetic investor-demo data (idempotent)."

    def handle(self, *args, **options):
        result = seed_demo()
        self.stdout.write(self.style.SUCCESS(json.dumps(result, indent=2)))
