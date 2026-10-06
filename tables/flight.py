"""SQL for the flight table."""

from models import FlightListing

# Route names and the captain. The captain comes through a LEFT JOIN because
# unassigned flights are allowed.
FLIGHT_LISTING_SQL = """
    SELECT flight.flight_id,
           flight.flight_number,
           departure.destination_name,
           arrival.destination_name,
           flight.departure_date,
           flight.departure_time,
           flight.status,
           flight.aircraft_type,
           flight.flight_type,
           captain.first_name || ' ' || captain.last_name
    FROM flight
    JOIN destination AS departure
      ON departure.destination_id = flight.departure_destination_id
    JOIN destination AS arrival
      ON arrival.destination_id = flight.arrival_destination_id
    LEFT JOIN flight_pilot
      ON flight_pilot.flight_id = flight.flight_id
     AND flight_pilot.role = 'Captain'
    LEFT JOIN pilot AS captain
      ON captain.pilot_id = flight_pilot.pilot_id
"""


class FlightTable:
    """Queries against the flight table."""

    def __init__(self, conn):
        self._conn = conn

    def search(
        self,
        destination_id=None,
        status=None,
        date_from=None,
        date_to=None,
        departing_after=None,
    ):
        """Return flights matching any combination of the given filters."""
        clauses = []
        parameters = []

        if destination_id is not None:
            # Either end of the route. Written as OR rather than
            # IN (column, column), so we can benefit from the indexes.
            clauses.append(
                "(flight.departure_destination_id = ?"
                " OR flight.arrival_destination_id = ?)"
            )
            parameters.extend([destination_id, destination_id])
        if status is not None:
            clauses.append("flight.status = ?")
            parameters.append(status)
        if date_from is not None:
            clauses.append("flight.departure_date >= ?")
            parameters.append(date_from)
        if date_to is not None:
            clauses.append("flight.departure_date <= ?")
            parameters.append(date_to)
        if departing_after is not None:
            clauses.append("flight.departure_date || ' ' || flight.departure_time > ?")
            parameters.append(departing_after)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._conn.execute(
            f"""
            {FLIGHT_LISTING_SQL}
            {where}
            ORDER BY flight.departure_date, flight.departure_time
            """,
            parameters,
        ).fetchall()
        return [FlightListing(*row) for row in rows]

    def get_listing(self, flight_id):
        """Return one flight with its route names."""
        row = self._conn.execute(
            f"""
            {FLIGHT_LISTING_SQL}
            WHERE flight.flight_id = ?
            """,
            (flight_id,),
        ).fetchone()
        return FlightListing(*row) if row is not None else None

    def max_hazard_level(self, flight_id):
        """Return the highest/worst hazard level on a flight's route."""
        row = self._conn.execute(
            """
            SELECT MAX(departure.hazard_level, arrival.hazard_level)
            FROM flight
            JOIN destination AS departure
              ON departure.destination_id = flight.departure_destination_id
            JOIN destination AS arrival
              ON arrival.destination_id = flight.arrival_destination_id
            WHERE flight.flight_id = ?
            """,
            (flight_id,),
        ).fetchone()
        return int(row[0]) if row is not None else None

    def create(
        self,
        flight_number,
        departure_destination_id,
        arrival_destination_id,
        departure_date,
        departure_time,
        status,
        aircraft_type,
        flight_type,
    ):
        """Add a flight and return its new ID."""
        cursor = self._conn.execute(
            """
            INSERT INTO flight
                (flight_number, departure_destination_id, arrival_destination_id,
                 departure_date, departure_time, status, aircraft_type, flight_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                flight_number,
                departure_destination_id,
                arrival_destination_id,
                departure_date,
                departure_time,
                status,
                aircraft_type,
                flight_type,
            ),
        )
        new_id = cursor.lastrowid
        if new_id is None:
            raise RuntimeError("The flight was inserted but no row ID was returned.")
        return new_id

    def update_schedule(self, flight_id, departure_date, departure_time, status, aircraft_type):
        """Update a flight's schedule, status and craft."""
        self._conn.execute(
            """
            UPDATE flight
            SET departure_date = ?,
                departure_time = ?,
                status         = ?,
                aircraft_type  = ?
            WHERE flight_id = ?
            """,
            (departure_date, departure_time, status, aircraft_type, flight_id),
        )

    def delete(self, flight_id):
        """Delete a flight. Its crew assignments cascade delete too."""
        self._conn.execute("DELETE FROM flight WHERE flight_id = ?", (flight_id,))
