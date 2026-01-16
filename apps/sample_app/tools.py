from __future__ import annotations

import hashlib
import random
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from agents.tool import function_tool

AIRLINES: list[dict[str, str]] = [
    {"name": "Delta Air Lines", "code": "DL"},
    {"name": "United Airlines", "code": "UA"},
    {"name": "American Airlines", "code": "AA"},
    {"name": "Southwest", "code": "WN"},
    {"name": "Alaska Airlines", "code": "AS"},
    {"name": "JetBlue", "code": "B6"},
]
FARE_CLASSES = ["Economy", "Premium Economy", "Business", "First"]
AIRCRAFT = ["A220", "A320", "A321neo", "B737", "B787-8", "E175"]


def _seed_for_route(origin: str, destination: str, travel_date: str) -> int:
    seed_text = f"{origin.strip().lower()}|{destination.strip().lower()}|{travel_date.strip()}"
    digest = hashlib.sha256(seed_text.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _parse_date(travel_date: str) -> date:
    try:
        return date.fromisoformat(travel_date)
    except ValueError:
        return date.today()


def _price_for_flight_number(flight_number: str) -> float:
    digest = hashlib.sha256(flight_number.encode("utf-8")).hexdigest()
    base = 140 + (int(digest[:6], 16) % 620)
    return round(base + 24.95, 2)


@function_tool
def find_flight(origin: str, destination: str, travel_date: str) -> list[dict[str, Any]]:
    """Return mock flight options for a given route and date."""

    seed = _seed_for_route(origin, destination, travel_date)
    rng = random.Random(seed)
    flight_count = rng.randint(3, 5)
    depart_day = _parse_date(travel_date)
    base_hour = rng.randint(6, 18)

    flights: list[dict[str, Any]] = []
    for offset in range(flight_count):
        airline = rng.choice(AIRLINES)
        flight_number = f"{airline['code']}{rng.randint(100, 999)}"
        minute = rng.choice([0, 15, 30, 45])
        depart_time = datetime.combine(
            depart_day,
            time(hour=(base_hour + offset * 2) % 24, minute=minute),
        )
        duration_minutes = rng.randint(90, 360)
        arrive_time = depart_time + timedelta(minutes=duration_minutes)
        flights.append(
            {
                "flight_number": flight_number,
                "airline": airline["name"],
                "origin": origin,
                "destination": destination,
                "date": depart_day.isoformat(),
                "depart_time": depart_time.isoformat(timespec="minutes"),
                "arrive_time": arrive_time.isoformat(timespec="minutes"),
                "duration_minutes": duration_minutes,
                "stops": rng.choice([0, 0, 1]),
                "fare_class": rng.choice(FARE_CLASSES),
                "seats_left": rng.randint(3, 24),
                "aircraft": rng.choice(AIRCRAFT),
            }
        )
    return flights


@function_tool
def get_flight_price(flight_number: str) -> dict[str, Any]:
    """Return a mock price quote for a flight number."""

    amount = _price_for_flight_number(flight_number)
    return {
        "flight_number": flight_number,
        "currency": "USD",
        "amount": amount,
        "fare_basis": "ECO",
        "last_updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


@function_tool
def book_flight(flight_number: str) -> dict[str, Any]:
    """Return a mock booking confirmation for a flight number."""

    digest = hashlib.sha256(f"book|{flight_number}".encode("utf-8")).hexdigest()
    booking_id = f"PNR-{digest[:6].upper()}"
    amount = _price_for_flight_number(flight_number)
    return {
        "booking_id": booking_id,
        "flight_number": flight_number,
        "status": "confirmed",
        "ticketed": True,
        "currency": "USD",
        "amount": amount,
        "seat": f"{int(digest[6:8], 16) % 28 + 1}{chr(65 + (int(digest[8:10], 16) % 6))}",
        "fare_class": "Economy",
        "notes": "Mock booking only; no real reservation was created.",
    }


__all__ = ["book_flight", "find_flight", "get_flight_price"]
