"""SQL for the destination table."""

from models import DestinationFlightCount, DestinationListing

# Convert a hazard level to text.
HAZARD_LABEL_SQL = """
        CASE destination.hazard_level
            WHEN 1 THEN 'Low'
            WHEN 2 THEN 'Medium'
            WHEN 3 THEN 'High'
            WHEN 4 THEN 'Very High'
            ELSE 'Extreme'
        END
"""


class DestinationTable:
    """Queries against the destination table."""

    def __init__(self, conn):
        self._conn = conn

    def list_all(self):
        """Return every destination, ordered by name."""
        rows = self._conn.execute(
            f"""
            SELECT destination.destination_id,
                   destination.destination_code,
                   destination.destination_name,
                   destination.planet,
                   destination.region,
                   destination.hazard_level,
                   {HAZARD_LABEL_SQL}
            FROM destination
            ORDER BY destination.destination_name
            """
        ).fetchall()
        return [DestinationListing(*row) for row in rows]

    def get(self, destination_id):
        """Return one destination."""
        row = self._conn.execute(
            f"""
            SELECT destination.destination_id,
                   destination.destination_code,
                   destination.destination_name,
                   destination.planet,
                   destination.region,
                   destination.hazard_level,
                   {HAZARD_LABEL_SQL}
            FROM destination
            WHERE destination.destination_id = ?
            """,
            (destination_id,),
        ).fetchone()
        return DestinationListing(*row) if row is not None else None

    def create(self, destination_name, destination_code, planet, region, hazard_level):
        """Add a destination."""
        self._conn.execute(
            """
            INSERT INTO destination
                (destination_name, destination_code, planet, region, hazard_level)
            VALUES (?, ?, ?, ?, ?)
            """,
            (destination_name, destination_code, planet, region, hazard_level),
        )

    def update(self, destination_id, destination_name, destination_code, region, hazard_level):
        """Update a destination. (The planet is left out on purpose.)"""
        self._conn.execute(
            """
            UPDATE destination
            SET destination_name = ?,
                destination_code = ?,
                region           = ?,
                hazard_level     = ?
            WHERE destination_id = ?
            """,
            (destination_name, destination_code, region, hazard_level, destination_id),
        )

    def delete(self, destination_id):
        """Delete a destination. Blocked if there are flights referencing it."""
        self._conn.execute(
            "DELETE FROM destination WHERE destination_id = ?", (destination_id,)
        )

    def count_flights_per_destination(self, exclude_cancelled=False):
        """Count flights touching each destination, at either end of the route.

        A LEFT JOIN is used here to keep destinations with no flights.
        """
        rows = self._conn.execute(
            """
            SELECT destination.destination_code,
                   destination.destination_name,
                   destination.planet,
                   COUNT(flight.flight_id)
            FROM destination
            LEFT JOIN flight
                   ON (flight.departure_destination_id = destination.destination_id
                       OR flight.arrival_destination_id = destination.destination_id)
                  AND (? = 0 OR flight.status <> 'Cancelled')
            GROUP BY destination.destination_id,
                     destination.destination_code,
                     destination.destination_name,
                     destination.planet
            ORDER BY COUNT(flight.flight_id) DESC, destination.destination_name
            """,
            (int(exclude_cancelled),),
        ).fetchall()
        return [DestinationFlightCount(*row) for row in rows]
