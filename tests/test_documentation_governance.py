from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt
from markdown_it.token import Token

ROOT = Path(__file__).resolve().parents[1]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _tokens_with_children(tokens: Iterable[Token]) -> Iterable[Token]:
    for token in tokens:
        yield token
        if token.children:
            yield from _tokens_with_children(token.children)


def _resolved_local_links(source: Path) -> set[Path]:
    tokens = MarkdownIt("commonmark").parse(_read_text(source))
    destinations: set[Path] = set()

    for token in _tokens_with_children(tokens):
        if token.type != "link_open":
            continue

        href = token.attrGet("href")
        assert href is not None
        parsed = urlsplit(href)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue

        relative_path = Path(unquote(parsed.path))
        assert not relative_path.is_absolute(), (
            f"{source.relative_to(ROOT)} contains a root-relative local link: {href}. "
            "Use a path relative to the Markdown file so repository navigation works "
            "outside a hosted website."
        )

        destination = (source.parent / relative_path).resolve()
        assert destination.is_relative_to(ROOT), (
            f"{source.relative_to(ROOT)} links outside the repository: {href}."
        )
        assert destination.is_file(), (
            f"{source.relative_to(ROOT)} contains a broken local link: {href}. "
            f"Expected {destination.relative_to(ROOT)} to be a file."
        )
        destinations.add(destination)

    return destinations


def _assert_routes_to(source: Path, required: set[Path]) -> None:
    destinations = _resolved_local_links(source)
    missing = required - destinations
    assert not missing, (
        f"{source.relative_to(ROOT)} must contain Markdown links to: "
        f"{', '.join(str(path.relative_to(ROOT)) for path in sorted(missing))}."
    )


def test_agents_file_stays_short_and_routes_to_docs() -> None:
    agents_path = ROOT / "AGENTS.md"
    non_blank_lines = [
        line for line in _read_text(agents_path).splitlines() if line.strip()
    ]

    assert len(non_blank_lines) <= 80, (
        "AGENTS.md should stay a short routing map. Move durable architecture, "
        "operations, and quality details into docs/ and link them from AGENTS.md."
    )

    _assert_routes_to(
        agents_path,
        {
            ROOT / "docs/index.md",
            ROOT / "docs/ARCHITECTURE.md",
            ROOT / "docs/OPERATIONS.md",
            ROOT / "docs/QUALITY.md",
        },
    )


def test_docs_index_links_system_of_record_files() -> None:
    _assert_routes_to(
        ROOT / "docs/index.md",
        {
            ROOT / "docs/ARCHITECTURE.md",
            ROOT / "docs/OPERATIONS.md",
            ROOT / "docs/QUALITY.md",
            ROOT / "docs/LEGIBILITY_AUDIT.md",
        },
    )
