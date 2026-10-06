"""Enumerations and row types shared by the SQL and interface layers."""

from enum import StrEnum
from typing import NamedTuple


class FlightStatus(StrEnum):
    """Lifecycle of a flight."""

    SCHEDULED = "Scheduled"
    BOARDING = "Boarding"
    DELAYED = "Delayed"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class AircraftType(StrEnum):
    """Types of aircraft that are available."""

    FRIGATE = "Frigate"
    ORNITHOPTER = "Ornithopter"
    HEAVY_FREIGHTER = "Heavy Freighter"


class FlightType(StrEnum):
    """Purpose of a flight."""

    PASSENGER = "Passenger"
    CARGO = "Cargo"
    DIPLOMATIC = "Diplomatic"


class CrewRole(StrEnum):
    """Roles a pilot can have on a flight."""

    CAPTAIN = "Captain"
    FIRST_OFFICER = "First Officer"


class LicenceClass(StrEnum):
    """Pilot licence classes (A is the highest)."""

    A = "A"
    B = "B"
    C = "C"


# Table rows


class Pilot(NamedTuple):
    """One row of the pilot table."""

    pilot_id: int
    first_name: str
    last_name: str
    licence_class: str
    years_experience: int
    specialisation: str | None
    call_sign: str


# Read models


class DestinationListing(NamedTuple):
    """A destination with its hazard level."""

    destination_id: int
    destination_code: str
    destination_name: str
    planet: str
    region: str | None
    hazard_level: int
    hazard_label: str


class FlightListing(NamedTuple):
    """A flight with route names and its captain."""

    flight_id: int
    flight_number: str
    departure: str
    arrival: str
    departure_date: str
    departure_time: str
    status: str
    aircraft_type: str
    flight_type: str
    captain: str | None


class CrewMember(NamedTuple):
    """A pilot assigned to a flight."""

    pilot_id: int
    pilot_name: str
    call_sign: str
    licence_class: str
    role: str


class ScheduleEntry(NamedTuple):
    """A flight in a pilot's schedule."""

    flight_number: str
    role: str
    departure: str
    arrival: str
    departure_date: str
    departure_time: str
    status: str


class AvailablePilot(NamedTuple):
    """A pilot who can take a given flight, and whether they can captain it."""

    pilot_id: int
    pilot_name: str
    licence_class: str
    years_experience: int
    specialisation: str | None
    can_captain: str


# Report rows


class DestinationFlightCount(NamedTuple):
    """Flights departing from or arriving at a destination."""

    destination_code: str
    destination_name: str
    planet: str
    flight_count: int


class PilotFlightCount(NamedTuple):
    """A pilot's number of flights."""

    pilot_name: str
    call_sign: str
    licence_class: str
    total_flights: int
    as_captain: int
    as_first_officer: int
