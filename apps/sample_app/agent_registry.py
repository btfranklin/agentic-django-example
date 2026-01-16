from __future__ import annotations

from collections.abc import Callable
from typing import Any

from agents import Agent
from agents.models import get_default_model

from sample_app.prompts import load_prompt, prompt_to_text
from sample_app.tools import book_flight, find_flight, get_flight_price


def get_agent_registry() -> dict[str, Callable[[], Agent[Any]]]:
    def build_demo_agent() -> Agent[Any]:
        instructions = prompt_to_text(load_prompt("demo_agent"))
        return Agent(
            name="Demo Agent",
            instructions=instructions,
            model=get_default_model(),
            tools=[find_flight, get_flight_price, book_flight],
        )

    return {"demo": build_demo_agent}
