from __future__ import annotations

import asyncio
import json

import pytest
from agentic_django.types import JsonObject, json_value
from agents.tool import FunctionTool
from agents.tool_context import ToolContext
from sample_app.tools import book_flight, find_flight, get_flight_price


def _invoke_tool(tool: FunctionTool, args: dict[str, str]) -> object:
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


def _flight_options(value: object) -> list[JsonObject]:
    result = json_value(value)
    assert isinstance(result, list)
    flights: list[JsonObject] = []
    for flight in result:
        assert isinstance(flight, dict)
        flights.append(flight)
    return flights


def _json_object(value: object) -> JsonObject:
    result = json_value(value)
    assert isinstance(result, dict)
    return result


@pytest.mark.parametrize(
    "travel_date",
    ["not-a-date", "2026-02-30", "20261003", "2026-W40-6", " 2026-10-03"],
)
def test_find_flight_reports_invalid_date_as_tool_error(travel_date: str) -> None:
    args = {
        "origin": "PHX",
        "destination": "JFK",
        "travel_date": travel_date,
    }

    result = _invoke_tool(find_flight, args)

    assert result == "travel_date must use YYYY-MM-DD."


def test_find_flight_returns_requested_date_and_is_deterministic() -> None:
    travel_date = "2026-10-03"
    args = {
        "origin": "PHX",
        "destination": "JFK",
        "travel_date": travel_date,
    }
    flights = _flight_options(_invoke_tool(find_flight, args))
    repeated_flights = _flight_options(_invoke_tool(find_flight, args))

    assert flights == repeated_flights
    assert flights
    for flight in flights:
        date = flight["date"]
        depart_time = flight["depart_time"]
        assert isinstance(date, str)
        assert isinstance(depart_time, str)
        assert date == travel_date
        assert depart_time.startswith(travel_date)


def test_flights_quotes_and_bookings_use_the_same_fare_class_and_price() -> None:
    flights = _flight_options(
        _invoke_tool(
            find_flight,
            {"origin": "PHX", "destination": "JFK", "travel_date": "2026-10-03"},
        )
    )

    assert flights
    for flight in flights:
        flight_number = flight["flight_number"]
        assert isinstance(flight_number, str)
        quote = _json_object(
            _invoke_tool(get_flight_price, {"flight_number": flight_number})
        )
        booking = _json_object(
            _invoke_tool(book_flight, {"flight_number": flight_number})
        )
        assert flight["fare_class"] == quote["fare_class"] == booking["fare_class"]
        assert flight["fare_class"] == "Economy"
        assert quote["fare_basis"] == "ECO"
        assert quote["amount"] == booking["amount"]
