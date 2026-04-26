from __future__ import annotations

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_agents_file_stays_short_and_routes_to_docs() -> None:
    agents = _read_text("AGENTS.md")
    non_blank_lines = [line for line in agents.splitlines() if line.strip()]

    assert len(non_blank_lines) <= 80, (
        "AGENTS.md should stay a short routing map. Move durable architecture, "
        "operations, and quality details into docs/ and link them from AGENTS.md."
    )

    for expected in [
        "docs/index.md",
        "docs/ARCHITECTURE.md",
        "docs/OPERATIONS.md",
        "docs/QUALITY.md",
    ]:
        assert expected in agents, (
            f"AGENTS.md must route future agents to {expected}. Update AGENTS.md "
            "when the docs spine changes."
        )


def test_docs_index_links_system_of_record_files() -> None:
    index = _read_text("docs/index.md")

    required_docs = {
        "ARCHITECTURE.md": ROOT / "docs/ARCHITECTURE.md",
        "OPERATIONS.md": ROOT / "docs/OPERATIONS.md",
        "QUALITY.md": ROOT / "docs/QUALITY.md",
        "LEGIBILITY_AUDIT.md": ROOT / "docs/LEGIBILITY_AUDIT.md",
    }
    for link_target, doc_path in required_docs.items():
        assert doc_path.exists(), f"Missing docs system-of-record file: {doc_path}"
        assert link_target in index, (
            f"docs/index.md must link to {link_target} so agents can discover "
            "the repo knowledge base progressively."
        )


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
    dependencies = pyproject["project"]["dependencies"]
    matches = [
        dependency
        for dependency in dependencies
        if dependency.lower().startswith("agentic-django")
    ]

    assert len(matches) == 1, "pyproject.toml should declare one agentic-django dependency."
    dependency = matches[0]
    assert ">=" in dependency, (
        "agentic-django should use the repo dependency policy's >= lower-bound "
        "style unless a tighter bound is required."
    )
    assert "@" not in dependency and "file:" not in dependency, (
        "agentic-django must be consumed from PyPI in this example repo, not "
        "from a local path or direct URL."
    )
