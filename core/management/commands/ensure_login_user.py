"""
Create or update the shared team login from environment variables.

Runs on every deploy (idempotent). Set in Railway:
  APP_LOGIN_USER      — username (e.g. "anura")
  APP_LOGIN_PASSWORD  — the shared password

Changing APP_LOGIN_PASSWORD in Railway and redeploying rotates the password.
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create/update the team login user from APP_LOGIN_USER / APP_LOGIN_PASSWORD env vars."

    def handle(self, *args, **options):
        username = os.environ.get("APP_LOGIN_USER", "").strip()
        password = os.environ.get("APP_LOGIN_PASSWORD", "")
        if not username or not password:
            self.stdout.write("APP_LOGIN_USER / APP_LOGIN_PASSWORD not set; skipping.")
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(username=username)
        user.is_staff = True  # allows /admin access with the same login
        # Only re-hash if the password actually changed — re-hashing on every
        # deploy invalidates all active sessions (logs everyone out mid-use).
        if created or not user.check_password(password):
            user.set_password(password)
        user.save()
        self.stdout.write(f"{'Created' if created else 'Updated'} login user '{username}'.")
