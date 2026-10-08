from decimal import Decimal
from django.core.management.base import BaseCommand
from subscriptions.models import SubscriptionPlan


class Command(BaseCommand):
    help = "Create or update the default subscription plans."

    def handle(self, *args, **options):
        plans = [
            {
                "code": "free",
                "name": "Free",
                "price": Decimal("0.00"),
                "validity_days": None,
                "daily_limit_minutes": 60,
                "total_limit_minutes": None,
                "fair_use_minutes": None,
                "allowed_languages": ["en", "ta"],
                "all_languages": False,
                "ai_voice": False,
                "export_enabled": False,
                "api_access": False,
                "team_users": False,
                "priority_support": False,
                "display_order": 1,
            },
            {
                "code": "basic",
                "name": "Basic",
                "price": Decimal("299.00"),
                "validity_days": 30,
                "daily_limit_minutes": None,
                "total_limit_minutes": 600,
                "fair_use_minutes": None,
                "allowed_languages": [
                    "en", "ta", "hi", "te", "ml",
                    "kn", "fr", "de", "ja", "es",
                ],
                "all_languages": False,
                "ai_voice": False,
                "export_enabled": False,
                "api_access": False,
                "team_users": False,
                "priority_support": False,
                "display_order": 2,
            },
            {
                "code": "pro",
                "name": "Pro",
                "price": Decimal("999.00"),
                "validity_days": 30,
                "daily_limit_minutes": None,
                "total_limit_minutes": None,
                "fair_use_minutes": 6000,
                "allowed_languages": [],
                "all_languages": True,
                "ai_voice": True,
                "export_enabled": True,
                "api_access": False,
                "team_users": False,
                "priority_support": False,
                "display_order": 3,
            },
            {
                "code": "enterprise",
                "name": "Enterprise",
                "price": Decimal("4999.00"),
                "validity_days": 30,
                "daily_limit_minutes": None,
                "total_limit_minutes": None,
                "fair_use_minutes": 30000,
                "allowed_languages": [],
                "all_languages": True,
                "ai_voice": True,
                "export_enabled": True,
                "api_access": True,
                "team_users": True,
                "priority_support": True,
                "display_order": 4,
            },
        ]

        for data in plans:
            plan, created = SubscriptionPlan.objects.update_or_create(
                code=data["code"],
                defaults=data,
            )
            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action}: {plan.name}"))
