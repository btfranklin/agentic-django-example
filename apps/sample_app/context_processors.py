from __future__ import annotations

from django.conf import settings
from django.http import HttpRequest


def demo_mode(request: HttpRequest) -> dict[str, bool]:
    return {"demo_login_enabled": settings.DEBUG}
