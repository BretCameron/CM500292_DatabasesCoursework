"""Command line interface for the Interstellar Aviation flight database, inspired by Dune!

Run with `python main.py`.

To return the database to its seed state, run `python setup_db.py --reset`.

Each menu option calls one controller function.
"""

import sqlite3

from controllers import database, destination, flight, flight_pilot, pilot
from db import connect
from rules import ValidationError
from setup_db import build_database

TITLE = "Interstellar Aviation: Flight Management"

# Note: the first six options are the ones named in the assignment brief.
MENU = [
    ("Add a New Flight", flight.add_flight),
    ("View Flights by Criteria", flight.view_flights),
    ("Update Flight Information", flight.update_flight),
    ("Assign Pilot to Flight", flight_pilot.assign_pilot),
    ("View Pilot Schedule", flight_pilot.view_pilot_schedule),
    ("View/Update Destination Information", destination.view_or_update_destination),
    ("View Flight Details and Crew", flight.view_flight_details),
    ("Delete a Flight", flight.delete_flight),
    ("Unassign a Pilot from a Flight", flight_pilot.unassign_pilot),
    ("View Pilots", pilot.view_pilots),
    ("Add a Pilot", pilot.add_pilot),
    ("Update a Pilot", pilot.update_pilot),
    ("Delete a Pilot", pilot.delete_pilot),
    ("Add a Destination", destination.add_destination),
    ("Delete a Destination", destination.delete_destination),
    ("Report: Flights per Destination", destination.report_flights_per_destination),
    ("Report: Flights per Pilot", pilot.report_flights_per_pilot),
    ("Rebuild the Sample Data", database.rebuild_database),
]


def print_menu(options):
    """Print the numbered menu."""
    print(f"\n{TITLE}")
    print("=" * len(TITLE))
    for number, (label, _) in enumerate(options, start=1):
        print(f"  {number:>2}. {label}")
    print("   0. Exit")


def run_menu(options, conn):
    """Run the chosen option until the user exits."""
    print_menu(options)
    while True:
        answer = input("\nChoose an option: ").strip()
        if answer == "0":
            return
        if not answer.isdigit() or not 1 <= int(answer) <= len(options):
            print(f"\nPlease enter a number between 0 and {len(options)}.")
            continue

        label, action = options[int(answer) - 1]
        print(f"\n{label}")
        print("-" * len(label))
        try:
            action(conn)
        except ValidationError as error:
            print(f"\n{error}")
        except sqlite3.IntegrityError as error:
            print(f"\nThe database rejected that change: {error}")

        input("\nPress Enter to see the menu.")
        print_menu(options)


def main():
    """Open the database and run the menu."""
    if build_database():
        print("No database found, so a new one was built and seeded.")

    conn = connect()
    try:
        run_menu(MENU, conn)
        print("\nGoodbye.")
    except (KeyboardInterrupt, EOFError):
        print("\n\nGoodbye.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
