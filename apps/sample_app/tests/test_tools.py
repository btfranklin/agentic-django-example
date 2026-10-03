from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest
from agents.tool_context import ToolContext
from sample_app.tools import book_flight, find_flight, get_flight_price


def _invoke_tool(tool: Any, args: dict[str, Any]) -> Any:
    tool_arguments = json.dumps(args)
    return asyncio.run(
        tool.on_invoke_tool(
            ToolContext(
                context={},
                tool_name=tool.name,
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

    result = _invoke_tool(find_flight, args)

    assert result == "travel_date must use YYYY-MM-DD."
    assert not isinstance(result, list)


def test_find_flight_returns_requested_date_and_is_deterministic() -> None:
    travel_date = "2026-10-03"
    args: dict[str, Any] = {
        "origin": "PHX",
        "destination": "JFK",
        "travel_date": travel_date,
    }
    flights = _invoke_tool(find_flight, args)
    repeated_flights = _invoke_tool(find_flight, args)

    assert flights == repeated_flights
    assert flights
    assert all(flight["date"] == travel_date for flight in flights)
    assert all(flight["depart_time"].startswith(travel_date) for flight in flights)


def test_flights_quotes_and_bookings_use_the_same_fare_class_and_price() -> None:
    flights = _invoke_tool(
        find_flight,
        {"origin": "PHX", "destination": "JFK", "travel_date": "2026-10-03"},
    )

    assert flights
    for flight in flights:
        flight_number = flight["flight_number"]
        quote = _invoke_tool(get_flight_price, {"flight_number": flight_number})
        booking = _invoke_tool(book_flight, {"flight_number": flight_number})

        assert flight["fare_class"] == quote["fare_class"] == booking["fare_class"]
        assert flight["fare_class"] == "Economy"
        assert quote["fare_basis"] == "ECO"
        assert quote["amount"] == booking["amount"]
