"""SQL for the pilot table."""

from models import AvailablePilot, Pilot, PilotFlightCount
from rules import HAZARD_CLEARANCE_LEVEL

PILOT_COLUMNS = """
            pilot_id, first_name, last_name, licence_class, years_experience,
            specialisation, call_sign
"""


class PilotTable:
    """Queries against the pilot table."""

    def __init__(self, conn):
        self._conn = conn

    def list_all(self):
        """Return every pilot (ordered by surname)."""
        rows = self._conn.execute(
            f"""
            SELECT {PILOT_COLUMNS}
            FROM pilot
            ORDER BY last_name, first_name
            """
        ).fetchall()
        return [Pilot(*row) for row in rows]

    def get(self, pilot_id):
        """Return one pilot."""
        row = self._conn.execute(
            f"""
            SELECT {PILOT_COLUMNS}
            FROM pilot
            WHERE pilot_id = ?
            """,
            (pilot_id,),
        ).fetchone()
        return Pilot(*row) if row is not None else None

    def create(
        self,
        first_name,
        last_name,
        licence_class,
        years_experience,
        specialisation,
        call_sign,
    ):
        """Add a pilot."""
        self._conn.execute(
            """
            INSERT INTO pilot
                (first_name, last_name, licence_class, years_experience,
                 specialisation, call_sign)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                first_name,
                last_name,
                licence_class,
                years_experience,
                specialisation,
                call_sign,
            ),
        )

    def update(
        self,
        pilot_id,
        first_name,
        last_name,
        licence_class,
        years_experience,
        specialisation,
        call_sign,
    ):
        """Update a pilot's details."""
        self._conn.execute(
            """
            UPDATE pilot
            SET first_name       = ?,
                last_name        = ?,
                licence_class    = ?,
                years_experience = ?,
                specialisation   = ?,
                call_sign        = ?
            WHERE pilot_id = ?
            """,
            (
                first_name,
                last_name,
                licence_class,
                years_experience,
                specialisation,
                call_sign,
                pilot_id,
            ),
        )

    def delete(self, pilot_id):
        """Delete a pilot (blocked if there are existing assignments)."""
        self._conn.execute("DELETE FROM pilot WHERE pilot_id = ?", (pilot_id,))

    def count_flights_per_pilot(self):
        """Count each pilot's flights."""
        rows = self._conn.execute(
            """
            SELECT pilot.first_name || ' ' || pilot.last_name,
                   pilot.call_sign,
                   pilot.licence_class,
                   COUNT(flight_pilot.flight_id),
                   COUNT(CASE WHEN flight_pilot.role = 'Captain' THEN 1 END),
                   COUNT(CASE WHEN flight_pilot.role = 'First Officer' THEN 1 END)
            FROM pilot
            LEFT JOIN flight_pilot ON flight_pilot.pilot_id = pilot.pilot_id
            GROUP BY pilot.pilot_id,
                     pilot.first_name,
                     pilot.last_name,
                     pilot.call_sign,
                     pilot.licence_class
            ORDER BY COUNT(flight_pilot.flight_id) DESC, pilot.last_name, pilot.first_name
            """
        ).fetchall()
        return [PilotFlightCount(*row) for row in rows]

    def list_available_for_flight(self, flight_id, max_hazard_level):
        """Return pilots who can take the given flight.

        Excludes anyone already on it, and anyone holding another non-cancelled
        flight that day.
        """
        any_licence_may_captain = max_hazard_level < HAZARD_CLEARANCE_LEVEL
        rows = self._conn.execute(
            """
            SELECT pilot.pilot_id,
                   pilot.first_name || ' ' || pilot.last_name,
                   pilot.licence_class,
                   pilot.years_experience,
                   pilot.specialisation,
                   CASE
                       WHEN ? = 1 OR pilot.licence_class = 'A' THEN 'Yes'
                       ELSE 'No'
                   END
            FROM pilot
            WHERE NOT EXISTS (
                      SELECT 1
                      FROM flight_pilot
                      WHERE flight_pilot.flight_id = ?
                        AND flight_pilot.pilot_id = pilot.pilot_id
                  )
              AND NOT EXISTS (
                      SELECT 1
                      FROM flight_pilot AS booked_assignment
                      JOIN flight AS booked_flight
                        ON booked_flight.flight_id = booked_assignment.flight_id
                      JOIN flight AS target ON target.flight_id = ?
                      WHERE booked_assignment.pilot_id = pilot.pilot_id
                        AND booked_flight.flight_id <> target.flight_id
                        AND booked_flight.departure_date = target.departure_date
                        AND booked_flight.status <> 'Cancelled'
                        AND target.status <> 'Cancelled'
                  )
            ORDER BY pilot.licence_class, pilot.years_experience DESC
            """,
            (int(any_licence_may_captain), flight_id, flight_id),
        ).fetchall()
        return [AvailablePilot(*row) for row in rows]
