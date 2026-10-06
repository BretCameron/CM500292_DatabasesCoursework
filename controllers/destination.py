"""Destination menu actions."""

from models import FlightStatus
from rules import ValidationError, now_text
from tables.destination import DestinationTable
from tables.flight import FlightTable
from utils.display import print_record, print_table
from utils.prompts import (
    keep,
    prompt_id,
    prompt_int,
    prompt_text,
    prompt_yes_no,
)


def choose_destination(conn, label):
    """List the destinations and ask for one."""
    destinations = DestinationTable(conn).list_all()
    print_table(destinations)
    destination_id = prompt_id(label, [row.destination_id for row in destinations])
    if destination_id is None:
        return None
    return next(row for row in destinations if row.destination_id == destination_id)


def _prompt_code(default=None):
    """Ask for a three letter destination code, taking a default value if left blank."""
    label = "Destination code (3 letters)" if default is None else f"Destination code [{default}]"
    while True:
        answer = prompt_text(label, required=False)
        if answer is None:
            if default is not None:
                return default
            print("Please enter a code.")
            continue
        if len(answer) != 3:
            print("A destination code is exactly three letters.")
            continue
        return answer.upper()


def view_or_update_destination(conn):
    """Show a destination in detail, then offer to edit it."""
    destination = choose_destination(conn, "Destination ID to view")
    if destination is None:
        return

    print()
    print_record(destination)
    print("\nUpcoming flights:")
    print_table(
        FlightTable(conn).search(
            destination_id=destination.destination_id, departing_after=now_text()
        )
    )

    if prompt_yes_no(f"\nUpdate {destination.destination_name}?"):
        _update_destination(conn, destination)


def _update_destination(conn, current):
    """Edit a destination, keeping any fields that are left blank."""
    print("\nLeave a field blank to keep it. The planet cannot be changed.")
    name = prompt_text(f"Name [{current.destination_name}]", required=False)
    code = _prompt_code(current.destination_code)
    region = prompt_text(f"Region [{current.region or '-'}]", required=False)
    hazard_level = prompt_int(f"Hazard level [{current.hazard_level}]", 1, 5, required=False)

    table = DestinationTable(conn)
    with conn:
        table.update(
            current.destination_id,
            keep(name, current.destination_name),
            code,
            keep(region, current.region),
            keep(hazard_level, current.hazard_level),
        )
    print("\nDestination updated.")
    updated = table.get(current.destination_id)
    if updated is not None:
        print_record(updated)


def add_destination(conn):
    """Add a destination."""
    name = prompt_text("Destination name")
    code = _prompt_code()
    planet = prompt_text("Planet")
    region = prompt_text("Region (optional)", required=False)
    hazard_level = prompt_int("Hazard level (1 low to 5 extreme)", 1, 5)

    with conn:
        DestinationTable(conn).create(name, code, planet, region, hazard_level)
    print(f"\nAdded {name} ({code}).")


def delete_destination(conn):
    """Delete a destination, unless flights still use it."""
    destination = choose_destination(conn, "Destination ID to delete")
    if destination is None:
        return

    flights = FlightTable(conn).search(destination_id=destination.destination_id)
    if flights:
        print(f"\n{destination.destination_name} is still used by these flights:")
        print_table(flights)
        raise ValidationError(
            "Delete those flights first, or cancel them and keep the record."
        )

    if not prompt_yes_no(f"Delete {destination.destination_name}?"):
        print("\nNothing deleted.")
        return

    with conn:
        DestinationTable(conn).delete(destination.destination_id)
    print(f"\nDeleted {destination.destination_name}.")


def report_flights_per_destination(conn):
    """Report how many flights depart from or arrive at each destination."""
    exclude_cancelled = prompt_yes_no(f"Exclude {FlightStatus.CANCELLED.lower()} flights?")
    print("\nFlights per destination, counting either end of the route:")
    print_table(DestinationTable(conn).count_flights_per_destination(exclude_cancelled))
