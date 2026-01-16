from __future__ import annotations

from functools import lru_cache
from importlib import resources

from promptdown import StructuredPrompt

PROMPT_SUFFIX = ".prompt.md"


@lru_cache(maxsize=None)
def _promptdown_text(name: str) -> str:
    """Return the raw promptdown text for ``name`` (cached)."""

    resource = resources.files(__name__).joinpath(f"{name}{PROMPT_SUFFIX}")
    return resource.read_text(encoding="utf-8")


def load_prompt(name: str) -> StructuredPrompt:
    """Load ``name`` from the ``sample_app.prompts`` package."""

    return StructuredPrompt.from_promptdown_string(_promptdown_text(name))


def prompt_to_text(prompt: StructuredPrompt) -> str:
    """Return the primary promptdown message as plain text."""

    text = prompt.system_message or prompt.developer_message
    if not text and prompt.conversation:
        text = "\n\n".join(message.content for message in prompt.conversation)
    return text or ""


__all__ = ["load_prompt", "prompt_to_text"]
