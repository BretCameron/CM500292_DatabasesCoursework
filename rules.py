"""Business rules checked in Python before a write, for anything we cannot check in SQL."""

from datetime import datetime

from models import LicenceClass

# Hazard level at which a captain must hold a Class A licence.
HAZARD_CLEARANCE_LEVEL = 4


class ValidationError(Exception):
    """A broken rule with user-facing error message."""


def now_text():
    """Return the current local time as 'YYYY-MM-DD HH:MM'."""
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def validate_future_departure(departure_date, departure_time, now):
    """Check a departure is later than now (to the minute)."""
    if f"{departure_date} {departure_time}" <= now:
        raise ValidationError(
            f"Departure must be later than now ({now}). "
            f"Given {departure_date} {departure_time}."
        )


def validate_different_destinations(departure_id, arrival_id):
    """Check a flight does not depart from and arrive at the same place."""
    if departure_id == arrival_id:
        raise ValidationError("Departure and arrival destinations must differ.")


def validate_captain_clearance(licence_class, max_hazard_level):
    """Check the captain is valid for the most hazardous destination in the route."""
    if max_hazard_level >= HAZARD_CLEARANCE_LEVEL and licence_class != LicenceClass.A:
        raise ValidationError(
            f"A hazard level {max_hazard_level} route needs a Class A captain. "
            f"This pilot holds Class {licence_class}."
        )
