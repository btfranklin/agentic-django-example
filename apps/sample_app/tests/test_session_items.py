from __future__ import annotations

import pytest
from django.contrib.auth.models import AbstractBaseUser
from django.test import Client
from django.urls import reverse

from agentic_django.models import AgentSession, AgentSessionItem

pytestmark = pytest.mark.django_db


def _make_session(user: AbstractBaseUser, session_key: str) -> AgentSession:
    return AgentSession.objects.create(owner=user, session_key=session_key)


def test_session_items_htmx_renders_conversation(
    client_logged_in: Client,
    user: AbstractBaseUser,
) -> None:
    session = _make_session(user, "session-items")
    AgentSessionItem.objects.create(
        session=session,
        sequence=1,
        payload={"role": "user", "content": "Hello"},
    )
    AgentSessionItem.objects.create(
        session=session,
        sequence=2,
        payload={"role": "tool", "content": "Found"},
    )

    response = client_logged_in.get(
        reverse("agents:session-items", kwargs={"session_key": session.session_key}),
        **{"HTTP_HX_REQUEST": "true"},
    )

    assert response.status_code == 200
    content = response.content.decode()
    assert "agent-conversation" in content
    assert "Hello" in content
    assert "Found" in content


def test_session_items_returns_json_without_htmx(
    client_logged_in: Client,
    user: AbstractBaseUser,
) -> None:
    session = _make_session(user, "session-items-json")
    AgentSessionItem.objects.create(
        session=session,
        sequence=1,
        payload={"role": "user", "content": "Hello"},
    )

    response = client_logged_in.get(
        reverse("agents:session-items", kwargs={"session_key": session.session_key})
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_key"] == session.session_key
    assert payload["items"][0]["content"] == "Hello"


def test_session_items_formats_reasoning_event(
    client_logged_in: Client,
    user: AbstractBaseUser,
) -> None:
    session = _make_session(user, "session-reasoning")
    AgentSessionItem.objects.create(
        session=session,
        sequence=1,
        payload={"type": "reasoning", "summary": []},
    )

    response = client_logged_in.get(
        reverse("agents:session-items", kwargs={"session_key": session.session_key}),
        **{"HTTP_HX_REQUEST": "true"},
    )

    assert response.status_code == 200
    content = response.content.decode()
    assert "Thought for a moment" in content
    assert "<details" not in content


def test_session_items_formats_reasoning_summary_details(
    client_logged_in: Client,
    user: AbstractBaseUser,
) -> None:
    session = _make_session(user, "session-reasoning-summary")
    AgentSessionItem.objects.create(
        session=session,
        sequence=1,
        payload={"type": "reasoning", "summary": ["Used the map API."]},
    )

    response = client_logged_in.get(
        reverse("agents:session-items", kwargs={"session_key": session.session_key}),
        **{"HTTP_HX_REQUEST": "true"},
    )

    assert response.status_code == 200
    content = response.content.decode()
    assert "Thought for a moment" in content
    assert "<details" in content
    assert "Used the map API." in content
