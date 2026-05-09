from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from core.services import get_or_create_current_week


class Command(BaseCommand):
    help = "Simulate weekly run detection for a user and optional ISO date."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("--date", dest="current_date", help="ISO date such as 2026-05-11")

    def handle(self, *args, **options):
        User = get_user_model()
        try:
            user = User.objects.get(username=options["username"])
        except User.DoesNotExist as exc:
            raise CommandError("User not found.") from exc

        current_day = None
        if options.get("current_date"):
            current_day = date.fromisoformat(options["current_date"])

        weekly_run = get_or_create_current_week(user, current_day)
        self.stdout.write(
            self.style.SUCCESS(
                f"Active weekly run: {weekly_run.chapter_name} "
                f"{weekly_run.week_start.isoformat()} to {weekly_run.week_end.isoformat()}"
            )
        )
