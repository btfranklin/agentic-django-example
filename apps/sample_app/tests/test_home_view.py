from __future__ import annotations

import pytest
from django.contrib.auth.models import AbstractBaseUser
from django.test import Client
from django.urls import reverse
from django.test.utils import override_settings

from agentic_django.models import AgentSession, AgentSessionItem

pytestmark = pytest.mark.django_db


def test_home_requires_login(client: Client) -> None:
    response = client.get(reverse("sample_app:home"))

    assert response.status_code == 302
    assert reverse("sample_app:login") in response["Location"]


def test_home_creates_session_and_conversation_poll(
    client_logged_in: Client,
    user: AbstractBaseUser,
) -> None:
    response = client_logged_in.get(reverse("sample_app:home"))

    assert response.status_code == 200
    session_key = client_logged_in.session.get("agent_session_key")
    assert session_key is not None
    assert AgentSession.objects.filter(owner=user, session_key=session_key).exists()

    content = response.content.decode()
    assert f'hx-get="/agents/sessions/{session_key}/items/"' in content
    assert 'hx-trigger="run-update from:body"' in content
    assert 'hx-swap="innerHTML"' in content
    assert ">Send<" in content


@override_settings(DEBUG=True)
def test_demo_login_in_debug_creates_user(client: Client) -> None:
    response = client.get(reverse("sample_app:demo-login"))

    assert response.status_code == 302
    assert response["Location"] == reverse("sample_app:home")
    assert client.session.get("_auth_user_id") is not None


@override_settings(DEBUG=False)
def test_demo_login_redirects_when_not_debug(client: Client) -> None:
    response = client.get(reverse("sample_app:demo-login"))

    assert response.status_code == 302
    assert response["Location"] == reverse("sample_app:login")


def test_reset_session_creates_new_session(
    client_logged_in: Client,
    user: AbstractBaseUser,
) -> None:
    session_key = "session-to-reset"
    session = AgentSession.objects.create(owner=user, session_key=session_key)
    AgentSessionItem.objects.create(
        session=session,
        sequence=1,
        payload={"role": "user", "content": "Hello"},
    )
    client_logged_in.session["agent_session_key"] = session_key
    client_logged_in.session.save()

    response = client_logged_in.post(
        reverse("sample_app:reset"),
        data={"session_key": session_key},
    )

    assert response.status_code == 302
    new_key = client_logged_in.session.get("agent_session_key")
    assert new_key is not None
    assert new_key != session_key
    assert AgentSession.objects.filter(owner=user, session_key=new_key).exists()
    assert AgentSessionItem.objects.filter(session=session).count() == 0
