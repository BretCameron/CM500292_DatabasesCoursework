"""Flight menu actions."""

from controllers.destination import choose_destination
from models import AircraftType, CrewRole, FlightStatus, FlightType
from rules import (
    now_text,
    validate_captain_clearance,
    validate_different_destinations,
    validate_future_departure,
)
from tables.flight import FlightTable
from tables.flight_pilot import FlightPilotTable
from tables.pilot import PilotTable
from utils.display import print_record, print_table
from utils.prompts import (
    keep,
    prompt_choice,
    prompt_date,
    prompt_id,
    prompt_optional_choice,
    prompt_text,
    prompt_time,
    prompt_yes_no,
)


def choose_flight(conn, label, flights=None):
    """List flights and ask the user to choose one."""
    if flights is None:
        flights = FlightTable(conn).search()
    print_table(flights)
    flight_id = prompt_id(label, [flight.flight_id for flight in flights])
    if flight_id is None:
        return None
    return next(flight for flight in flights if flight.flight_id == flight_id)


def choose_upcoming_flight(conn, label):
    """List flights that haven't departed yet and ask the user to choose one."""
    flights = FlightTable(conn).search(departing_after=now_text())
    if not flights:
        print("There are no upcoming flights. Add one with 'Add a New Flight'.")
        return None
    return choose_flight(conn, label, flights)


def _assign_new_crew(conn, flight_id, max_hazard_level):
    """Offer to assign a captain and a first officer to a new flight."""
    crew = FlightPilotTable(conn)
    for role in (CrewRole.CAPTAIN, CrewRole.FIRST_OFFICER):
        available = PilotTable(conn).list_available_for_flight(flight_id, max_hazard_level)
        if role == CrewRole.CAPTAIN:
            cleared = [pilot for pilot in available if pilot.can_captain == "Yes"]
            if len(cleared) < len(available):
                print("\nOnly pilots cleared for this route are offered as captain.")
            available = cleared
        if not available:
            print(f"\nNo pilot is free to take this flight as {role.lower()}.")
            continue

        print(f"\nPilots available as {role.lower()}:")
        print_table(available)
        pilot_id = prompt_id(
            f"Pilot ID for {role.lower()}",
            [pilot.pilot_id for pilot in available],
            blank_hint=f"blank for no {role.lower()}",
        )
        if pilot_id is None:
            continue
        chosen = next(pilot for pilot in available if pilot.pilot_id == pilot_id)
        if role == CrewRole.CAPTAIN:
            validate_captain_clearance(chosen.licence_class, max_hazard_level)
        crew.assign(flight_id, pilot_id, role)
        print(f"{chosen.pilot_name} assigned as {role.lower()}.")


def add_flight(conn):
    """Add a flight, then offer to select its crew."""
    flights = FlightTable(conn)
    flight_number = prompt_text("Flight number").upper()

    print("\nDeparture destination:")
    departure = choose_destination(conn, "Departure destination ID")
    if departure is None:
        return
    print("\nArrival destination:")
    arrival = choose_destination(conn, "Arrival destination ID")
    if arrival is None:
        return
    validate_different_destinations(departure.destination_id, arrival.destination_id)

    now = now_text()
    print(f"\nThe flight must depart later than now ({now}).")
    departure_date = prompt_date("Departure date")
    departure_time = prompt_time("Departure time")
    validate_future_departure(departure_date, departure_time, now)

    print("\nAircraft type:")
    aircraft_type = prompt_choice("Aircraft", list(AircraftType))
    print("\nFlight type:")
    flight_type = prompt_choice("Flight type", list(FlightType))

    # A rejected crew assignment takes the flight with it.
    with conn:
        flight_id = flights.create(
            flight_number,
            departure.destination_id,
            arrival.destination_id,
            departure_date,
            departure_time,
            FlightStatus.SCHEDULED,
            aircraft_type,
            flight_type,
        )
        print(
            f"\nAdded {flight_number}: {departure.destination_name} to "
            f"{arrival.destination_name} on {departure_date} at {departure_time}."
        )
        if prompt_yes_no("Assign crew now?"):
            _assign_new_crew(
                conn, flight_id, max(departure.hazard_level, arrival.hazard_level)
            )


def view_flights(conn):
    """Search flights by destination, status and departure date range."""
    print("Every filter is optional and they combine. Leave one blank to skip it.")

    destination_id = None
    if prompt_yes_no("Filter by destination?"):
        destination = choose_destination(conn, "Destination ID")
        if destination is not None:
            destination_id = destination.destination_id

    print("\nStatus:")
    status = prompt_optional_choice("Status", list(FlightStatus))
    date_from = prompt_date(
        "Earliest departure date", blank_hint="blank for any", required=False
    )
    date_to = prompt_date("Latest departure date", blank_hint="blank for any", required=False)

    print()
    print_table(
        FlightTable(conn).search(
            destination_id=destination_id,
            status=status,
            date_from=date_from,
            date_to=date_to,
        )
    )


def update_flight(conn):
    """Update a flight's date, time, status or craft."""
    flights = FlightTable(conn)
    current = choose_flight(conn, "Flight ID to update")
    if current is None:
        return

    print()
    print_record(current)
    print("\nLeave a field blank to keep it. The route cannot be changed.")
    departure_date = prompt_date(f"Departure date [{current.departure_date}]", required=False)
    departure_time = prompt_time(f"Departure time [{current.departure_time}]", required=False)
    print("\nStatus:")
    status = prompt_optional_choice(
        "Status", list(FlightStatus), zero_label=f"Keep {current.status}"
    )
    print("\nAircraft:")
    aircraft_type = prompt_optional_choice(
        "Aircraft", list(AircraftType), zero_label=f"Keep {current.aircraft_type}"
    )

    new_date = keep(departure_date, current.departure_date)
    new_time = keep(departure_time, current.departure_time)
    if departure_date is not None or departure_time is not None:
        validate_future_departure(new_date, new_time, now_text())

    with conn:
        flights.update_schedule(
            current.flight_id,
            new_date,
            new_time,
            keep(status, current.status),
            keep(aircraft_type, current.aircraft_type),
        )
    print("\nFlight updated.")
    updated = flights.get_listing(current.flight_id)
    if updated is not None:
        print_record(updated)


def view_flight_details(conn):
    """Show one flight with its crew."""
    chosen = choose_flight(conn, "Flight ID to view")
    if chosen is None:
        return

    print()
    print_record(chosen)
    print("\nCrew:")
    print_table(FlightPilotTable(conn).list_crew(chosen.flight_id))


def delete_flight(conn):
    """Delete a flight and its crew assignments."""
    chosen = choose_flight(conn, "Flight ID to delete")
    if chosen is None:
        return

    crew = FlightPilotTable(conn).list_crew(chosen.flight_id)
    if crew:
        print(f"\nThese assignments will go with {chosen.flight_number}:")
        print_table(crew)
    print("\nTo call a flight off but keep the record, update its status to Cancelled.")
    if not prompt_yes_no(f"Delete {chosen.flight_number}?"):
        print("\nNothing deleted.")
        return

    with conn:
        FlightTable(conn).delete(chosen.flight_id)
    print(f"\nDeleted {chosen.flight_number}.")
