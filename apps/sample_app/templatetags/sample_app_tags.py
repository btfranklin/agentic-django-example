from __future__ import annotations

import json
import re
from typing import Any

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

from agentic_django.serializers import _to_jsonable

register = template.Library()

_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_ITALIC_RE = re.compile(r"\*(.+?)\*")
_ITALIC_UNDERSCORE_RE = re.compile(r"_(.+?)_")


def _format_inline(text: str) -> str:
    escaped = escape(text)
    escaped = _BOLD_RE.sub(r"<strong>\1</strong>", escaped)
    escaped = _ITALIC_RE.sub(r"<em>\1</em>", escaped)
    escaped = _ITALIC_UNDERSCORE_RE.sub(r"<em>\1</em>", escaped)
    return escaped


def _render_markdown(text: str) -> str:
    lines = text.splitlines()
    html_parts: list[str] = []
    paragraph_lines: list[str] = []
    current_list: str | None = None

    def flush_paragraph() -> None:
        if paragraph_lines:
            formatted = "<br>".join(_format_inline(line) for line in paragraph_lines)
            html_parts.append(f"<p>{formatted}</p>")
            paragraph_lines.clear()

    def close_list() -> None:
        nonlocal current_list
        if current_list:
            html_parts.append(f"</{current_list}>")
            current_list = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            close_list()
            continue

        ul_match = re.match(r"^[-*]\s+(.*)$", stripped)
        ol_match = re.match(r"^\d+\.\s+(.*)$", stripped)
        if ul_match or ol_match:
            flush_paragraph()
            list_type = "ul" if ul_match else "ol"
            item_text = ul_match.group(1) if ul_match else ol_match.group(1)
            if current_list != list_type:
                close_list()
                html_parts.append(f"<{list_type}>")
                current_list = list_type
            html_parts.append(f"<li>{_format_inline(item_text)}</li>")
            continue

        close_list()
        paragraph_lines.append(line)

    flush_paragraph()
    close_list()
    return "\n".join(html_parts) if html_parts else "<p></p>"


def _extract_content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
                    continue
                refusal = item.get("refusal")
                if isinstance(refusal, str):
                    parts.append(refusal)
        return "\n".join(parts)
    return str(content) if content is not None else ""


def _format_json_like(value: Any) -> str:
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return ""
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            return value
        return json.dumps(parsed, indent=2, sort_keys=True, ensure_ascii=False)
    return json.dumps(_to_jsonable(value), indent=2, sort_keys=True, ensure_ascii=False)


def _extract_output_text(output: Any) -> str:
    if isinstance(output, str):
        return output
    if isinstance(output, list):
        texts: list[str] = []
        for item in output:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    texts.append(text)
        if texts:
            return "\n".join(texts)
    if isinstance(output, dict):
        text = output.get("text")
        if isinstance(text, str):
            return text
    return _format_json_like(output)


def _extract_summary_text(summary: Any) -> str:
    if isinstance(summary, str):
        return summary
    if isinstance(summary, list):
        parts: list[str] = []
        for item in summary:
            if isinstance(item, str):
                parts.append(item)
                continue
            if isinstance(item, dict):
                text = item.get("text") or item.get("summary")
                if isinstance(text, str):
                    parts.append(text)
                    continue
            if item is not None:
                parts.append(str(item))
        return "\n".join(part for part in parts if part)
    if isinstance(summary, dict):
        text = summary.get("text") or summary.get("summary")
        if isinstance(text, str):
            return text
    if summary is None:
        return ""
    return _format_json_like(summary)


@register.filter
def pretty_json(value: Any) -> str:
    jsonable = _to_jsonable(value)
    if isinstance(jsonable, str):
        text = jsonable.replace("\\n", "\n")
        return mark_safe(escape(text))
    payload = json.dumps(jsonable, indent=2, sort_keys=True, ensure_ascii=False)
    payload = payload.replace("\\n", "\n")
    return mark_safe(escape(payload))


@register.filter
def render_output(value: Any) -> str:
    jsonable = _to_jsonable(value)
    if isinstance(jsonable, str):
        return mark_safe(_render_markdown(jsonable))
    payload = json.dumps(jsonable, indent=2, sort_keys=True, ensure_ascii=False)
    payload = payload.replace("\\n", "\n")
    return mark_safe(f"<pre>{escape(payload)}</pre>")


@register.filter
def session_item_context(value: Any) -> dict[str, Any]:
    jsonable = _to_jsonable(value)
    context = {
        "kind": "event",
        "label": "Event",
        "body": "<pre></pre>",
        "meta": "",
        "is_code": True,
    }
    if isinstance(jsonable, dict):
        role = jsonable.get("role")
        item_type = jsonable.get("type")
        if role in {"user", "assistant", "system", "developer"} or item_type == "message":
            text = _extract_content_text(jsonable.get("content"))
            label = (role or "assistant").replace("_", " ").title()
            context.update(
                {
                    "kind": role or "assistant",
                    "label": label,
                    "body": _render_markdown(text),
                    "meta": "",
                    "is_code": False,
                }
            )
            return context
        if item_type == "function_call":
            name = jsonable.get("name") or "tool"
            arguments = _format_json_like(jsonable.get("arguments", ""))
            call_id = jsonable.get("call_id") or ""
            context.update(
                {
                    "kind": "tool",
                    "label": f"Tool call: {name}",
                    "body": f"<pre>{escape(arguments)}</pre>",
                    "meta": call_id,
                    "is_code": True,
                }
            )
            return context
        if item_type == "function_call_output":
            output = jsonable.get("output", "")
            output_text = _extract_output_text(output)
            call_id = jsonable.get("call_id") or ""
            context.update(
                {
                    "kind": "tool-output",
                    "label": "Tool output",
                    "body": f"<pre>{escape(output_text)}</pre>",
                    "meta": call_id,
                    "is_code": True,
                }
            )
            return context
        if item_type == "reasoning":
            summary = jsonable.get("summary")
            summary_text = _extract_summary_text(summary)
            details_html = ""
            if summary_text.strip():
                details_html = (
                    '<details class="thread-item__details">'
                    "<summary>Details</summary>"
                    f"<pre>{escape(summary_text)}</pre>"
                    "</details>"
                )
            context.update(
                {
                    "kind": "reasoning",
                    "label": "Reasoning",
                    "body": f"<p>💭 Thought for a moment.</p>{details_html}",
                    "meta": "",
                    "is_code": False,
                }
            )
            return context

    fallback = _format_json_like(jsonable)
    context["body"] = f"<pre>{escape(fallback)}</pre>"
    return context
