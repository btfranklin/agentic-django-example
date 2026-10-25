from __future__ import annotations

import pytest
from agentic_django.models import AgentSession, AgentSessionItem
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.test import Client
from django.urls import reverse

pytestmark = pytest.mark.django_db


def _make_session(user: User, session_key: str) -> AgentSession:
    return AgentSession.objects.create(owner=user, session_key=session_key)


def test_session_items_htmx_renders_conversation(
    client_logged_in: Client,
    user: User,
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
        payload={"type": "function_call_output", "call_id": "call-1", "output": "Found"},
    )

    response = client_logged_in.get(
        reverse("agents:session-items", kwargs={"session_key": session.session_key}),
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    content = response.content.decode()
    assert "agent-conversation" in content
    assert "Hello" in content
    assert "Found" in content


def test_session_items_returns_json_without_htmx(
    client_logged_in: Client,
    user: User,
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
    user: User,
) -> None:
    session = _make_session(user, "session-reasoning")
    AgentSessionItem.objects.create(
        session=session,
        sequence=1,
        payload={"type": "reasoning", "id": "reasoning-1", "summary": []},
    )

    response = client_logged_in.get(
        reverse("agents:session-items", kwargs={"session_key": session.session_key}),
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    content = response.content.decode()
    assert "Thought for a moment" in content
    assert "<details" not in content


@pytest.mark.parametrize("htmx", [False, True])
def test_session_items_preserves_reasoning_summary(
    client_logged_in: Client,
    user: User,
    htmx: bool,
) -> None:
    session = _make_session(user, "session-reasoning-summary")
    AgentSessionItem.objects.create(
        session=session,
        sequence=1,
        payload={
            "type": "reasoning",
            "id": "reasoning-1",
            "summary": [{"type": "summary_text", "text": "Used the map API."}],
        },
    )

    response = client_logged_in.get(
        reverse("agents:session-items", kwargs={"session_key": session.session_key}),
        HTTP_HX_REQUEST="true" if htmx else "false",
    )

    assert response.status_code == 200
    if htmx:
        content = response.content.decode()
        assert "Thought for a moment" in content
        assert "<details" in content
        assert "Used the map API." in content
        assert "ValidatorIterator" not in content
    else:
        assert response.json()["items"] == [
            {
                "type": "reasoning",
                "id": "reasoning-1",
                "summary": [{"type": "summary_text", "text": "Used the map API."}],
            }
        ]


@pytest.mark.parametrize("role", [["user"], {"name": "user"}, 42])
def test_malformed_roles_render_as_escaped_events(
    role: object,
) -> None:
    content = render_to_string(
        "agentic_django/partials/conversation.html",
        {
            "items": [
                {
                    "payload": {
                        "type": "message",
                        "role": role,
                        "content": "<script>unsafe()</script>",
                    }
                }
            ]
        },
    )
    assert "Event" in content
    assert "&lt;script&gt;unsafe()&lt;/script&gt;" in content
    assert "<script>unsafe()</script>" not in content


def test_tool_arguments_over_integer_limit_keep_their_text(
    client_logged_in: Client,
    user: User,
) -> None:
    session = _make_session(user, "session-large-integer")
    arguments = "9" * 5000
    AgentSessionItem.objects.create(
        session=session,
        sequence=1,
        payload={
            "type": "function_call",
            "call_id": "call-1",
            "name": "test_tool",
            "arguments": arguments,
        },
    )

    response = client_logged_in.get(
        reverse("agents:session-items", kwargs={"session_key": session.session_key}),
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    assert arguments in response.content.decode()
