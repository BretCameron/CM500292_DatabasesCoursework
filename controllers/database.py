"""Database maintenance menu actions."""

from setup_db import rebuild
from tables.destination import DestinationTable
from tables.flight import FlightTable
from tables.pilot import PilotTable
from utils.prompts import prompt_yes_no


def rebuild_database(conn):
    """Restore the sample data, discarding everything currently stored."""
    print(
        "This deletes every destination, pilot, flight and crew assignment, "
        "then restores the sample data."
    )
    if not prompt_yes_no("Rebuild the database?"):
        print("\nNothing changed.")
        return

    rebuild(conn)
    print(
        f"\nRebuilt: {len(DestinationTable(conn).list_all())} destinations, "
        f"{len(PilotTable(conn).list_all())} pilots and "
        f"{len(FlightTable(conn).search())} flights."
    )
