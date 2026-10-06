"""Pilot menu actions."""

from models import LicenceClass
from rules import ValidationError
from tables.flight_pilot import FlightPilotTable
from tables.pilot import PilotTable
from utils.display import print_record, print_table
from utils.prompts import (
    keep,
    prompt_choice,
    prompt_id,
    prompt_int,
    prompt_optional_choice,
    prompt_text,
    prompt_yes_no,
)


def choose_pilot(conn, label):
    """List pilots and ask the user to choose one."""
    pilots = PilotTable(conn).list_all()
    print_table(pilots)
    pilot_id = prompt_id(label, [pilot.pilot_id for pilot in pilots])
    if pilot_id is None:
        return None
    return next(pilot for pilot in pilots if pilot.pilot_id == pilot_id)


def view_pilots(conn):
    """List every pilot."""
    print_table(PilotTable(conn).list_all())


def add_pilot(conn):
    """Add a pilot."""
    first_name = prompt_text("First name")
    last_name = prompt_text("Surname")

    print("\nOnly Class A pilots may captain a route at hazard level 4 or above.")
    licence_class = prompt_choice("Licence class", list(LicenceClass))
    years_experience = prompt_int("Years of experience", 0)
    specialisation = prompt_text("Specialisation (optional, such as Long-Haul)", required=False)
    call_sign = prompt_text("Call sign")

    with conn:
        PilotTable(conn).create(
            first_name,
            last_name,
            licence_class,
            years_experience,
            specialisation,
            call_sign,
        )
    print(f"\nAdded {first_name} {last_name} ({call_sign}).")


def update_pilot(conn):
    """Update a pilot, keeping any field that's been left blank.

    A downgraded licence is not re-checked against flights the pilot already
    captains (out of scope).
    """
    current = choose_pilot(conn, "Pilot ID to update")
    if current is None:
        return

    print(f"\nEditing {current.first_name} {current.last_name}. Leave a field blank to keep it.")
    first_name = prompt_text(f"First name [{current.first_name}]", required=False)
    last_name = prompt_text(f"Surname [{current.last_name}]", required=False)
    print("Licence class:")
    licence_class = prompt_optional_choice(
        "Licence", list(LicenceClass), zero_label=f"Keep Class {current.licence_class}"
    )
    years_experience = prompt_int(
        f"Years of experience [{current.years_experience}]", 0, required=False
    )
    specialisation = prompt_text(
        f"Specialisation [{current.specialisation or '-'}]", required=False
    )
    call_sign = prompt_text(f"Call sign [{current.call_sign}]", required=False)

    table = PilotTable(conn)
    with conn:
        table.update(
            current.pilot_id,
            keep(first_name, current.first_name),
            keep(last_name, current.last_name),
            keep(licence_class, current.licence_class),
            keep(years_experience, current.years_experience),
            keep(specialisation, current.specialisation),
            keep(call_sign, current.call_sign),
        )
    print("\nPilot updated.")
    updated = table.get(current.pilot_id)
    if updated is not None:
        print_record(updated)


def delete_pilot(conn):
    """Delete a pilot, unless they're still assigned to a flight."""
    pilot = choose_pilot(conn, "Pilot ID to delete")
    if pilot is None:
        return

    schedule = FlightPilotTable(conn).list_schedule(pilot.pilot_id)
    if schedule:
        print(f"\n{pilot.first_name} {pilot.last_name} is still assigned to these flights:")
        print_table(schedule)
        raise ValidationError("Unassign the pilot from those flights first.")

    if not prompt_yes_no(f"Delete {pilot.first_name} {pilot.last_name}?"):
        print("\nNothing deleted.")
        return

    with conn:
        PilotTable(conn).delete(pilot.pilot_id)
    print(f"\nDeleted {pilot.first_name} {pilot.last_name}.")


def report_flights_per_pilot(conn):
    """Report each pilot's workload."""
    print("Flights per pilot, including cancelled flights:")
    print_table(PilotTable(conn).count_flights_per_pilot())
