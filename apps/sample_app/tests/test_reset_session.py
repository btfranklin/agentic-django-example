from __future__ import annotations

from typing import Any, ClassVar

import pytest
from agentic_django.conf import get_settings
from agentic_django.models import AgentRun, AgentSession, AgentSessionItem
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.test import Client
from django.urls import reverse

pytestmark = pytest.mark.django_db


class MockSessionBackend:
    cleared_keys: ClassVar[list[str]] = []

    def __init__(self, session_key: str) -> None:
        self.session_key = session_key

    @classmethod
    def get_or_create(cls, session_key: str, owner: Any) -> MockSessionBackend:
        del owner
        return cls(session_key)

    async def clear_session(self) -> None:
        self.cleared_keys.append(self.session_key)


def _set_active_session(client: Client, session_key: str) -> None:
    session = client.session
    session["agent_session_key"] = session_key
    session.save()


def _add_history(session: AgentSession) -> AgentSessionItem:
    return AgentSessionItem.objects.create(
        session=session,
        sequence=1,
        payload={"role": "user", "content": "Keep this history"},
    )


@pytest.mark.parametrize("status", [AgentRun.Status.PENDING, AgentRun.Status.RUNNING])
def test_reset_rejects_active_run_and_keeps_key_and_history(
    client_logged_in: Client,
    user: AbstractBaseUser,
    status: str,
) -> None:
    session_key = f"session-{status}"
    _set_active_session(client_logged_in, session_key)
    session = AgentSession.objects.create(owner=user, session_key=session_key)
    history_item = _add_history(session)
    AgentRun.objects.create(
        session=session,
        owner=user,
        agent_key="demo",
        status=status,
        input_payload="A pending request",
    )

    response = client_logged_in.post(
        reverse("sample_app:reset"),
        data={"session_key": session_key},
    )

    assert response.status_code == 409
    assert client_logged_in.session["agent_session_key"] == session_key
    assert AgentSessionItem.objects.filter(pk=history_item.pk).exists()


@pytest.mark.parametrize("status", [AgentRun.Status.COMPLETED, AgentRun.Status.FAILED])
def test_reset_clears_terminal_session_history_and_rotates_key(
    client_logged_in: Client,
    user: AbstractBaseUser,
    status: str,
) -> None:
    session_key = f"session-{status}"
    _set_active_session(client_logged_in, session_key)
    session = AgentSession.objects.create(owner=user, session_key=session_key)
    _add_history(session)
    AgentRun.objects.create(
        session=session,
        owner=user,
        agent_key="demo",
        status=status,
        input_payload="A finished request",
    )

    response = client_logged_in.post(
        reverse("sample_app:reset"),
        data={"session_key": session_key},
    )

    assert response.status_code == 302
    new_key = client_logged_in.session["agent_session_key"]
    assert new_key != session_key
    assert not AgentSessionItem.objects.filter(session=session).exists()
    assert AgentSession.objects.filter(owner=user, session_key=new_key).exists()


def test_reset_clears_configured_backend_and_local_history(
    client_logged_in: Client,
    user: AbstractBaseUser,
    settings: Any,
) -> None:
    MockSessionBackend.cleared_keys.clear()
    settings.AGENTIC_DJANGO_SESSION_BACKEND = (
        f"{__name__}.MockSessionBackend"
    )
    assert get_settings().session_backend == settings.AGENTIC_DJANGO_SESSION_BACKEND
    session_key = "session-custom-backend"
    _set_active_session(client_logged_in, session_key)
    session = AgentSession.objects.create(owner=user, session_key=session_key)
    _add_history(session)

    response = client_logged_in.post(
        reverse("sample_app:reset"),
        data={"session_key": session_key},
    )

    assert response.status_code == 302
    assert MockSessionBackend.cleared_keys == [session_key]
    assert not AgentSessionItem.objects.filter(session=session).exists()


def test_reset_handles_missing_session_and_rotates_key(client_logged_in: Client) -> None:
    missing_key = "missing-session"
    _set_active_session(client_logged_in, missing_key)

    response = client_logged_in.post(
        reverse("sample_app:reset"),
        data={"session_key": missing_key},
    )

    assert response.status_code == 302
    assert client_logged_in.session["agent_session_key"] != missing_key


def test_reset_requires_login(client: Client) -> None:
    response = client.post(
        reverse("sample_app:reset"),
        data={"session_key": "private-session"},
    )

    assert response.status_code == 302
    assert reverse("sample_app:login") in response["Location"]


def test_reset_rejects_get(client_logged_in: Client) -> None:
    response = client_logged_in.get(reverse("sample_app:reset"))

    assert response.status_code == 405


def test_reset_does_not_clear_another_owners_session(
    client_logged_in: Client,
) -> None:
    other_user = get_user_model().objects.create_user(
        username="other-user",
        password="password",
    )
    session_key = "other-users-session"
    other_session = AgentSession.objects.create(
        owner=other_user,
        session_key=session_key,
    )
    history_item = _add_history(other_session)

    response = client_logged_in.post(
        reverse("sample_app:reset"),
        data={"session_key": session_key},
    )

    assert response.status_code == 302
    assert AgentSessionItem.objects.filter(pk=history_item.pk).exists()
    assert AgentSession.objects.filter(owner=other_user, session_key=session_key).exists()
    assert client_logged_in.session.get("agent_session_key") != session_key


def test_reset_requires_csrf_token(user: AbstractBaseUser) -> None:
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)

    response = client.post(
        reverse("sample_app:reset"),
        data={"session_key": "session-without-csrf"},
    )

    assert response.status_code == 403
