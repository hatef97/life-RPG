from django.db import OperationalError, ProgrammingError

from .services import ensure_profile, get_or_create_current_week


class WeeklyRunMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(request, "user", None) and request.user.is_authenticated:
            try:
                ensure_profile(request.user)
                request.weekly_run = get_or_create_current_week(request.user)
            except (OperationalError, ProgrammingError):
                request.weekly_run = None
        return self.get_response(request)
