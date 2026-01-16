from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.test import Client
from django.urls import reverse

from agentic_django.models import AgentRun, AgentSession

pytestmark = pytest.mark.django_db


def _patch_enqueue(monkeypatch: pytest.MonkeyPatch) -> None:
    def _noop(_: str) -> None:
        return None

    monkeypatch.setattr("agentic_django.views.enqueue_agent_run", _noop)


def _make_session(user: AbstractBaseUser, session_key: str) -> AgentSession:
    return AgentSession.objects.create(owner=user, session_key=session_key)


def test_run_create_htmx_returns_fragment_and_creates_run(
    client_logged_in: Client,
    user: AbstractBaseUser,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_enqueue(monkeypatch)
    session_key = "session-key"

    response = client_logged_in.post(
        reverse("agents:run-create"),
        data={"session_key": session_key, "input": "Hello"},
        **{"HTTP_HX_REQUEST": "true"},
    )

    assert response.status_code == 200
    run = AgentRun.objects.get(owner=user, session__session_key=session_key)
    assert run.status == AgentRun.Status.PENDING

    content = response.content.decode()
    assert f'data-run-id="{run.id}"' in content
    assert f'id="run-container-{run.id}"' in content
    assert f'hx-get="/agents/runs/{run.id}/fragment/"' in content


def test_run_create_returns_json_without_htmx(
    client_logged_in: Client,
    user: AbstractBaseUser,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_enqueue(monkeypatch)
    session_key = "session-key-json"

    response = client_logged_in.post(
        reverse("agents:run-create"),
        data={"session_key": session_key, "input": "Hello"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == AgentRun.Status.PENDING
    assert AgentRun.objects.filter(owner=user, session__session_key=session_key).exists()


def test_run_create_rejects_unknown_agent_key(
    client_logged_in: Client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_enqueue(monkeypatch)
    response = client_logged_in.post(
        reverse("agents:run-create"),
        data={
            "session_key": "session-key",
            "input": "Hello",
            "agent_key": "missing",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"] == "Unknown agent_key"


def test_run_create_requires_input(
    client_logged_in: Client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_enqueue(monkeypatch)
    response = client_logged_in.post(
        reverse("agents:run-create"),
        data={"session_key": "session-key"},
    )

    assert response.status_code == 400
    assert response.json()["error"] == "input is required"


def test_run_fragment_for_running_includes_polling(
    client_logged_in: Client,
    user: AbstractBaseUser,
) -> None:
    session = _make_session(user, "session-running")
    run = AgentRun.objects.create(
        session=session,
        owner=user,
        agent_key="demo",
        status=AgentRun.Status.RUNNING,
        input_payload="Hello",
        task_id="",
    )

    response = client_logged_in.get(
        reverse("agents:run-fragment", kwargs={"run_id": run.id})
    )

    assert response.status_code == 200
    content = response.content.decode()
    assert "Running" in content
    assert f'hx-get="/agents/runs/{run.id}/fragment/"' in content


def test_run_fragment_completed_hides_output(
    client_logged_in: Client,
    user: AbstractBaseUser,
) -> None:
    session = _make_session(user, "session-completed")
    run = AgentRun.objects.create(
        session=session,
        owner=user,
        agent_key="demo",
        status=AgentRun.Status.COMPLETED,
        input_payload="Hello",
        final_output={"answer": "done"},
        task_id="",
    )

    response = client_logged_in.get(
        reverse("agents:run-fragment", kwargs={"run_id": run.id})
    )

    assert response.status_code == 200
    content = response.content.decode()
    assert "Completed" in content
    assert "agent-run__output" not in content
    assert "done" not in content


def test_run_detail_returns_json(
    client_logged_in: Client,
    user: AbstractBaseUser,
) -> None:
    session = _make_session(user, "session-detail")
    run = AgentRun.objects.create(
        session=session,
        owner=user,
        agent_key="demo",
        status=AgentRun.Status.PENDING,
        input_payload="Hello",
        task_id="",
    )

    response = client_logged_in.get(
        reverse("agents:run-detail", kwargs={"run_id": run.id})
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == str(run.id)
    assert payload["status"] == AgentRun.Status.PENDING


def test_run_detail_requires_owner(
    client_logged_in: Client,
    user: AbstractBaseUser,
) -> None:
    session = _make_session(user, "session-owner")
    run = AgentRun.objects.create(
        session=session,
        owner=user,
        agent_key="demo",
        status=AgentRun.Status.PENDING,
        input_payload="Hello",
        task_id="",
    )
    user_model = get_user_model()
    other_user = user_model.objects.create_user(username="other-user", password="pass")
    client_logged_in.force_login(other_user)

    response = client_logged_in.get(
        reverse("agents:run-detail", kwargs={"run_id": run.id})
    )

    assert response.status_code == 404
