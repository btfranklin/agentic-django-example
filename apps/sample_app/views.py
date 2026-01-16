from __future__ import annotations

import uuid
from typing import Any

from asgiref.sync import async_to_sync
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from agentic_django.models import AgentRun, AgentSession, AgentSessionItem
from agentic_django.signals import agent_session_created
from agentic_django.sessions import get_session


def demo_login(request: HttpRequest) -> HttpResponse:
    if not settings.DEBUG:
        return redirect("sample_app:login")

    user_model = get_user_model()
    user, created = user_model.objects.get_or_create(username="demo")
    if created:
        user.set_password("demo")
        user.save(update_fields=["password"])
    login(request, user)
    return redirect("sample_app:home")


@login_required
def home(request: HttpRequest) -> HttpResponse:
    session_key = request.session.get("agent_session_key")
    if not session_key:
        session_key = uuid.uuid4().hex
        request.session["agent_session_key"] = session_key

    session, created = AgentSession.objects.get_or_create(
        owner=request.user,
        session_key=session_key,
    )
    if created:
        agent_session_created.send(sender=AgentSession, session=session)
    latest_run = None
    if session:
        latest_run = (
            AgentRun.objects.filter(owner=request.user, session=session)
            .order_by("-created_at")
            .first()
        )

    context: dict[str, Any] = {
        "session_key": session_key,
        "latest_run": latest_run,
        "session": session,
    }
    return render(request, "sample_app/home.html", context)


@login_required
@require_POST
def reset_session(request: HttpRequest) -> HttpResponse:
    session_key = request.POST.get("session_key") or request.session.get("agent_session_key")
    if session_key:
        session = AgentSession.objects.filter(
            owner=request.user,
            session_key=session_key,
        ).first()
        if session:
            backend_session = get_session(session_key, request.user)
            async_to_sync(backend_session.clear_session)()
            AgentSessionItem.objects.filter(session=session).delete()
    new_session_key = uuid.uuid4().hex
    request.session["agent_session_key"] = new_session_key
    session, created = AgentSession.objects.get_or_create(
        owner=request.user,
        session_key=new_session_key,
    )
    if created:
        agent_session_created.send(sender=AgentSession, session=session)
    return redirect("sample_app:home")
