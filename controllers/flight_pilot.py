"""Crew menu actions (i.e. assigning pilots to flights)."""

from controllers.flight import choose_flight, choose_upcoming_flight
from controllers.pilot import choose_pilot
from models import CrewRole
from rules import ValidationError, now_text, validate_captain_clearance
from tables.flight import FlightTable
from tables.flight_pilot import FlightPilotTable
from tables.pilot import PilotTable
from utils.display import print_table
from utils.prompts import prompt_choice, prompt_id, prompt_yes_no


def _departure(entry):
    return f"{entry.departure_date} {entry.departure_time}"


def assign_pilot(conn):
    """Assign a pilot to an upcoming flight."""
    flight = choose_upcoming_flight(conn, "Flight ID to crew")
    if flight is None:
        return

    crew_table = FlightPilotTable(conn)
    crew = crew_table.list_crew(flight.flight_id)
    if crew:
        print(f"\nCurrent crew on {flight.flight_number}:")
        print_table(crew)

    filled = {member.role for member in crew}
    free_roles = [role for role in CrewRole if role not in filled]
    if not free_roles:
        raise ValidationError(
            f"{flight.flight_number} already has a captain and a first officer. "
            "Unassign one of them first."
        )

    hazard_level = FlightTable(conn).max_hazard_level(flight.flight_id)
    if hazard_level is None:
        raise ValidationError("That flight no longer exists.")

    available = PilotTable(conn).list_available_for_flight(flight.flight_id, hazard_level)
    if not available:
        raise ValidationError(
            "No pilots are free for that date. Everyone is either on this flight "
            "already or flying that day."
        )
    print(f"\nPilots available for {flight.flight_number}:")
    print_table(available)
    print(
        "Pilots left out are already on this flight, or hold another "
        "non-cancelled flight that day."
    )
    pilot_id = prompt_id("Pilot ID", [pilot.pilot_id for pilot in available])
    if pilot_id is None:
        return
    chosen = next(pilot for pilot in available if pilot.pilot_id == pilot_id)

    print("\nRole:")
    role = prompt_choice("Role", free_roles)
    if role == CrewRole.CAPTAIN:
        validate_captain_clearance(chosen.licence_class, hazard_level)

    with conn:
        crew_table.assign(flight.flight_id, pilot_id, role)
    print(f"\n{chosen.pilot_name} assigned to {flight.flight_number} as {role.lower()}.")


def view_pilot_schedule(conn):
    """Show a pilot's upcoming and past flights."""
    pilot = choose_pilot(conn, "Pilot ID")
    if pilot is None:
        return

    schedule = FlightPilotTable(conn).list_schedule(pilot.pilot_id)
    now = now_text()
    upcoming = [entry for entry in schedule if _departure(entry) > now]
    past = [entry for entry in schedule if _departure(entry) <= now]

    print(f"\nSchedule for {pilot.first_name} {pilot.last_name} ({pilot.call_sign}).")
    print("\nUpcoming flights:")
    print_table(upcoming)
    print("\nPast flights:")
    print_table(past)


def unassign_pilot(conn):
    """Remove a pilot from a flight."""
    flight = choose_flight(conn, "Flight ID")
    if flight is None:
        return

    crew_table = FlightPilotTable(conn)
    crew = crew_table.list_crew(flight.flight_id)
    if not crew:
        raise ValidationError(f"{flight.flight_number} has no crew assigned.")

    print(f"\nCrew on {flight.flight_number}:")
    print_table(crew)
    pilot_id = prompt_id("Pilot ID to unassign", [member.pilot_id for member in crew])
    if pilot_id is None:
        return
    chosen = next(member for member in crew if member.pilot_id == pilot_id)

    if not prompt_yes_no(f"Remove {chosen.pilot_name} from {flight.flight_number}?"):
        print("\nNothing changed.")
        return

    with conn:
        crew_table.unassign(flight.flight_id, pilot_id)
    print(f"\n{chosen.pilot_name} removed from {flight.flight_number}.")
