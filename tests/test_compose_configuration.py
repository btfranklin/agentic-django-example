from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("docker") is None, reason="Docker CLI is not installed")
def test_compose_passes_app_configuration(tmp_path: Path) -> None:
    environment_file = tmp_path / ".env"
    environment_file.write_text("", encoding="utf-8")
    overrides = {
        "DJANGO_SECRET_KEY": "test-secret",
        "DJANGO_DEBUG": "false",
        "DJANGO_ALLOWED_HOSTS": "demo.example,localhost",
        "OPENAI_API_KEY": "test-key",
        "OPENAI_DEFAULT_MODEL": "test-model",
        "DATABASE_URL": "postgresql://user:pass@database/demo",
        "TASKS_BACKEND": "django_tasks.backends.immediate.ImmediateBackend",
        "REDIS_URL": "redis://localhost:6379/0",
    }
    result = subprocess.run(
        ["docker", "compose", "--env-file", str(environment_file), "config", "--format", "json"],
        cwd=ROOT,
        env={**os.environ, **overrides},
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    configuration = json.loads(result.stdout)
    for name in ("web", "rqworker", "migrate"):
        environment = configuration["services"][name]["environment"]
        for key in (
            "DJANGO_SECRET_KEY", "DJANGO_DEBUG", "DJANGO_ALLOWED_HOSTS",
            "OPENAI_API_KEY", "OPENAI_DEFAULT_MODEL", "DATABASE_URL",
        ):
            assert environment[key] == overrides[key]
        assert environment["TASKS_BACKEND"] == "django_tasks_rq.RQBackend"
        assert environment["REDIS_URL"] == "redis://redis:6379/0"
    for name in ("web", "rqworker"):
        assert configuration["services"][name]["depends_on"]["migrate"]["condition"] == (
            "service_completed_successfully"
        )
