from __future__ import annotations

from collections.abc import Callable
from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils.deprecation import MiddlewareMixin
from django_htmx.http import HttpResponseStopPolling


class AgentLoginMiddleware(MiddlewareMixin):
    """Keep expired logins out of agent fragments."""

    def process_view(
        self,
        request: HttpRequest,
        view_func: Callable[..., HttpResponse],
        view_args: tuple[Any, ...],
        view_kwargs: dict[str, Any],
    ) -> HttpResponse | None:
        match = request.resolver_match
        if (
            match is None
            or match.namespace != "agents"
            or not request.htmx
            or request.user.is_authenticated
        ):
            return None
        if match.url_name == "run-fragment":
            return HttpResponseStopPolling(
                render_to_string("sample_app/login_required.html", request=request)
            )
        return JsonResponse(
            {"error": "Your session has ended. Sign in again before you send a request."},
            status=401,
        )
