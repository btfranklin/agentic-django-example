from __future__ import annotations

import pytest
from agentic_django.models import AgentRun
from django.test import Client
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_expired_login_does_not_accept_htmx_submission(client: Client) -> None:
    response = client.post(
        reverse("agents:run-create"),
        {"session_key": "expired", "input": "Keep this draft"},
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 401
    assert "Sign in again" in response.json()["error"]
    assert not AgentRun.objects.exists()
    assert "Location" not in response


def test_expired_login_stops_polling_and_returns_home_after_login(client: Client) -> None:
    response = client.get(
        reverse("agents:run-fragment", kwargs={"run_id": "00000000-0000-0000-0000-000000000001"}),
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 286
    content = response.content.decode()
    assert "Your session has ended." in content
    assert 'href="/login/?next=/"' in content
    assert "hx-get=" not in content
    assert "<html" not in content


def test_expired_login_keeps_login_document_out_of_conversation(client: Client) -> None:
    response = client.get(
        reverse("agents:session-items", kwargs={"session_key": "expired"}),
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 401
    assert response["Content-Type"] == "application/json"
    assert "Location" not in response


def test_non_htmx_agent_request_still_redirects_to_login(client: Client) -> None:
    response = client.post(reverse("agents:run-create"), {"input": "Hello"})

    assert response.status_code == 302
    assert response["Location"].startswith(reverse("sample_app:login"))
