from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest
from agents.tool_context import ToolContext
from sample_app.tools import find_flight


def _invoke_find_flight(args: dict[str, Any]) -> Any:
    tool_arguments = json.dumps(args)
    return asyncio.run(
        find_flight.on_invoke_tool(
            ToolContext(
                context={},
                tool_name=find_flight.name,
                tool_call_id="call-test",
                tool_arguments=tool_arguments,
            ),
            tool_arguments,
        )
    )


@pytest.mark.parametrize(
    "travel_date",
    ["not-a-date", "2026-02-30", "20261003", "2026-W40-6", " 2026-10-03"],
)
def test_find_flight_reports_invalid_date_as_tool_error(travel_date: str) -> None:
    args: dict[str, Any] = {
        "origin": "PHX",
        "destination": "JFK",
        "travel_date": travel_date,
    }

    result = _invoke_find_flight(args)

    assert result == "travel_date must use YYYY-MM-DD."
    assert not isinstance(result, list)


def test_find_flight_returns_requested_date_and_is_deterministic() -> None:
    travel_date = "2026-10-03"
    args: dict[str, Any] = {
        "origin": "PHX",
        "destination": "JFK",
        "travel_date": travel_date,
    }
    flights = _invoke_find_flight(args)
    repeated_flights = _invoke_find_flight(args)

    assert flights == repeated_flights
    assert flights
    assert all(flight["date"] == travel_date for flight in flights)
    assert all(flight["depart_time"].startswith(travel_date) for flight in flights)
