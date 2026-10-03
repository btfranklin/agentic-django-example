from __future__ import annotations

import os
import runpy
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("entrypoint", ["manage", "wsgi", "asgi"])
@pytest.mark.parametrize("process_override", [False, True])
def test_entrypoints_load_env_file(
    tmp_path: Path, entrypoint: str, process_override: bool
) -> None:
    shutil.copytree(ROOT / "agentic_django_example", tmp_path / "agentic_django_example")
    shutil.copytree(ROOT / "apps", tmp_path / "apps")
    shutil.copy(ROOT / "manage.py", tmp_path / "manage.py")
    (tmp_path / ".env").write_text(
        "DJANGO_SECRET_KEY=file-secret\n"
        "DJANGO_DEBUG=false\n"
        "OPENAI_API_KEY=file-test-key\n"
        "OPENAI_DEFAULT_MODEL=file-test-model\n"
        "TASKS_BACKEND=django_tasks.backends.immediate.ImmediateBackend\n"
        "REDIS_URL=redis://localhost:6379/0\n",
        encoding="utf-8",
    )
    environment = os.environ.copy()
    for name in (
        "DJANGO_SECRET_KEY", "DJANGO_DEBUG", "OPENAI_API_KEY", "OPENAI_DEFAULT_MODEL",
        "TASKS_BACKEND", "REDIS_URL", "DATABASE_URL", "PYTHON_DOTENV_DISABLED",
    ):
        environment.pop(name, None)
    if process_override:
        environment["DJANGO_SECRET_KEY"] = "process-secret"
        environment["OPENAI_API_KEY"] = "process-test-key"
    bootstrap = (
        "import manage; manage.main()"
        if entrypoint == "manage"
        else f"import agentic_django_example.{entrypoint}"
    )
    code = (
        "import os, sys; sys.argv = ['manage.py', 'check']; "
        f"{bootstrap}; "
        "from django.conf import settings; "
        f"assert settings.SECRET_KEY == {'process-secret' if process_override else 'file-secret'!r}; "
        f"assert os.environ['OPENAI_API_KEY'] == {'process-test-key' if process_override else 'file-test-key'!r}; "
        "assert os.environ['OPENAI_DEFAULT_MODEL'] == 'file-test-model'; "
        "assert settings.DEBUG is False; "
        "assert settings.TASKS['default']['BACKEND'] == "
        "'django_tasks.backends.immediate.ImmediateBackend'; "
        "assert settings.REDIS_URL == 'redis://localhost:6379/0'"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr


def test_postgres_url_preserves_credentials_and_connection_options(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://demo%40host:p%23ss%3Aword@db:5433/demo%20name"
        "?sslmode=require&connect_timeout=10&application_name=agentic%20demo",
    )
    configuration = runpy.run_path(str(ROOT / "agentic_django_example/settings.py"))
    database = configuration["DATABASES"]["default"]

    assert database["USER"] == "demo@host"
    assert database["PASSWORD"] == "p#ss:word"
    assert database["NAME"] == "demo name"
    assert database["HOST"] == "db"
    assert database["PORT"] == 5433
    assert database["OPTIONS"] == {
        "sslmode": "require",
        "connect_timeout": "10",
        "application_name": "agentic demo",
    }


def test_database_url_rejects_unsupported_database_scheme(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")
    monkeypatch.setenv("DATABASE_URL", "mysql://user:password@db/example")

    with pytest.raises(ImproperlyConfigured, match="postgres or postgresql"):
        runpy.run_path(str(ROOT / "agentic_django_example/settings.py"))
