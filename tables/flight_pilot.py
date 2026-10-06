"""SQL for the flight_pilot table, which assigns pilots to flights."""

from models import CrewMember, ScheduleEntry


class FlightPilotTable:
    """Queries against the flight_pilot table."""

    def __init__(self, conn):
        self._conn = conn

    def list_crew(self, flight_id):
        """Return the pilots assigned to a flight (captain first)."""
        rows = self._conn.execute(
            """
            SELECT pilot.pilot_id,
                   pilot.first_name || ' ' || pilot.last_name,
                   pilot.call_sign,
                   pilot.licence_class,
                   flight_pilot.role
            FROM flight_pilot
            JOIN pilot ON pilot.pilot_id = flight_pilot.pilot_id
            WHERE flight_pilot.flight_id = ?
            ORDER BY flight_pilot.role
            """,
            (flight_id,),
        ).fetchall()
        return [CrewMember(*row) for row in rows]

    def assign(self, flight_id, pilot_id, role):
        """Assign a pilot to a flight in the given role."""
        self._conn.execute(
            "INSERT INTO flight_pilot (flight_id, pilot_id, role) VALUES (?, ?, ?)",
            (flight_id, pilot_id, role),
        )

    def unassign(self, flight_id, pilot_id):
        """Remove a pilot from a flight."""
        self._conn.execute(
            "DELETE FROM flight_pilot WHERE flight_id = ? AND pilot_id = ?",
            (flight_id, pilot_id),
        )

    def list_schedule(self, pilot_id):
        """Return every flight a pilot is assigned to (earliest first)."""
        rows = self._conn.execute(
            """
            SELECT flight.flight_number,
                   flight_pilot.role,
                   departure.destination_name,
                   arrival.destination_name,
                   flight.departure_date,
                   flight.departure_time,
                   flight.status
            FROM flight_pilot
            JOIN flight ON flight.flight_id = flight_pilot.flight_id
            JOIN destination AS departure
              ON departure.destination_id = flight.departure_destination_id
            JOIN destination AS arrival
              ON arrival.destination_id = flight.arrival_destination_id
            WHERE flight_pilot.pilot_id = ?
            ORDER BY flight.departure_date, flight.departure_time
            """,
            (pilot_id,),
        ).fetchall()
        return [ScheduleEntry(*row) for row in rows]
