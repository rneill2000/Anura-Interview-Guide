"""Require login for every page except the login page itself and static files."""

from django.conf import settings
from django.shortcuts import redirect


EXEMPT_PREFIXES = (
    "/login",
    "/static/",
    "/favicon.ico",
)


class LoginRequiredMiddleware:
    """
    Site-wide auth gate. Everything — including API endpoints like the
    Bullhorn search and guide generation — requires a signed-in session.
    New routes are protected automatically without needing a decorator.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if not request.user.is_authenticated and not any(
            path.startswith(p) for p in EXEMPT_PREFIXES
        ):
            return redirect(f"{settings.LOGIN_URL}?next={path}")
        return self.get_response(request)
