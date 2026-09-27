from __future__ import annotations

import json
import tomllib
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]


def _read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_validation_entrypoints_are_declared() -> None:
    pyproject = tomllib.loads(_read_text("pyproject.toml"))
    scripts = pyproject["tool"]["pdm"]["scripts"]

    for script_name in ["lint", "test", "check"]:
        assert script_name in scripts, (
            f"pyproject.toml must expose `pdm run {script_name}` as a stable "
            "validation entrypoint."
        )

    package_json = json.loads(_read_text("package.json"))
    assert "build:css" in package_json["scripts"], (
        "package.json must keep `npm run build:css` available so frontend asset "
        "work has a stable entrypoint."
    )


def test_agentic_django_dependency_stays_pypi_based() -> None:
    pyproject = tomllib.loads(_read_text("pyproject.toml"))
    requirements = [
        Requirement(dependency) for dependency in pyproject["project"]["dependencies"]
    ]
    matches = [
        requirement
        for requirement in requirements
        if canonicalize_name(requirement.name) == "agentic-django"
    ]

    assert len(matches) == 1, "pyproject.toml should declare one agentic-django dependency."
    requirement = matches[0]
    assert any(specifier.operator == ">=" for specifier in requirement.specifier), (
        "agentic-django should use the repo dependency policy's >= lower-bound "
        "style unless a tighter bound is required."
    )
    assert requirement.url is None, (
        "agentic-django must be consumed from PyPI in this example repo, not "
        "from a local path or direct URL."
    )


def test_rq_backend_loads_with_project_settings() -> None:
    from django.test import override_settings
    from django_tasks import task_backends
    from django_tasks_rq import RQBackend

    with override_settings(
        TASKS={"default": {"BACKEND": "django_tasks_rq.RQBackend"}}
    ):
        backend = task_backends["default"]
        assert isinstance(backend, RQBackend)
        assert list(backend.check()) == []
