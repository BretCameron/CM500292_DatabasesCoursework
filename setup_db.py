"""Build and seed the flight management database.

To rebuild the database, run: python setup_db.py --reset
"""

import argparse

from db import DEFAULT_DB_PATH, connect

# Order is important here: drop children tables ahead of parents.
DROP_SQL = """
DROP TABLE IF EXISTS flight_pilot;
DROP TABLE IF EXISTS flight;
DROP TABLE IF EXISTS pilot;
DROP TABLE IF EXISTS destination;
"""

SCHEMA_SQL = """
CREATE TABLE destination (
    destination_id   INTEGER     PRIMARY KEY,
    destination_name VARCHAR(60) NOT NULL UNIQUE,
    destination_code CHAR(3)     NOT NULL UNIQUE CHECK (length(destination_code) = 3),
    planet           VARCHAR(60) NOT NULL,
    region           VARCHAR(60),
    hazard_level     INTEGER     NOT NULL CHECK (hazard_level BETWEEN 1 AND 5)
);

CREATE TABLE pilot (
    pilot_id         INTEGER     PRIMARY KEY,
    first_name       VARCHAR(40) NOT NULL,
    last_name        VARCHAR(40) NOT NULL,
    licence_class    CHAR(1)     NOT NULL CHECK (licence_class IN ('A', 'B', 'C')),
    years_experience INTEGER     NOT NULL CHECK (years_experience >= 0),
    specialisation   VARCHAR(60),
    call_sign        VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE flight (
    flight_id                INTEGER     PRIMARY KEY,
    flight_number            VARCHAR(10) NOT NULL UNIQUE,
    departure_destination_id INTEGER     NOT NULL
        REFERENCES destination (destination_id) ON DELETE RESTRICT,
    arrival_destination_id   INTEGER     NOT NULL
        REFERENCES destination (destination_id) ON DELETE RESTRICT,
    departure_date           CHAR(10)    NOT NULL CHECK (date(departure_date) IS departure_date),
    departure_time           CHAR(5)     NOT NULL
        CHECK (time(departure_time) IS departure_time || ':00' AND departure_time < '24:00'),
    status                   VARCHAR(10) NOT NULL DEFAULT 'Scheduled'
        CHECK (status IN ('Scheduled', 'Boarding', 'Delayed', 'Completed', 'Cancelled')),
    aircraft_type            VARCHAR(20) NOT NULL
        CHECK (aircraft_type IN ('Frigate', 'Ornithopter', 'Heavy Freighter')),
    flight_type              VARCHAR(12) NOT NULL
        CHECK (flight_type IN ('Passenger', 'Cargo', 'Diplomatic')),
    CHECK (departure_destination_id <> arrival_destination_id)
);

CREATE TABLE flight_pilot (
    flight_id INTEGER     NOT NULL REFERENCES flight (flight_id) ON DELETE CASCADE,
    pilot_id  INTEGER     NOT NULL REFERENCES pilot (pilot_id)   ON DELETE RESTRICT,
    role      VARCHAR(20) NOT NULL CHECK (role IN ('Captain', 'First Officer')),
    PRIMARY KEY (flight_id, pilot_id),
    UNIQUE (flight_id, role)
);


-- INDEXES

CREATE INDEX idx_flight_departure_destination_id ON flight (departure_destination_id);
CREATE INDEX idx_flight_arrival_destination_id   ON flight (arrival_destination_id);

CREATE INDEX idx_flight_departure_date_time ON flight (departure_date, departure_time);

CREATE INDEX idx_flight_pilot_pilot_id ON flight_pilot (pilot_id);


-- DOUBLE-BOOKING TRIGGERS
-- Reject a pilot who has two non-cancelled flights on the same date.

-- Assigning a pilot to a flight
CREATE TRIGGER flight_pilot_prevent_double_booking_insert
BEFORE INSERT ON flight_pilot
WHEN EXISTS (
    SELECT 1
    FROM flight_pilot AS booked_assignment
    JOIN flight AS booked_flight ON booked_flight.flight_id = booked_assignment.flight_id
    JOIN flight AS target_flight ON target_flight.flight_id = NEW.flight_id
    WHERE booked_assignment.pilot_id = NEW.pilot_id
      AND booked_assignment.flight_id <> NEW.flight_id
      AND booked_flight.departure_date = target_flight.departure_date
      AND booked_flight.status <> 'Cancelled'
      AND target_flight.status <> 'Cancelled'
)
BEGIN
    SELECT RAISE(ABORT, 'Pilot is already assigned to a flight on that date');
END;

-- Changing an existing assignment's pilot or flight
CREATE TRIGGER flight_pilot_prevent_double_booking_update
BEFORE UPDATE OF flight_id, pilot_id ON flight_pilot
WHEN EXISTS (
    SELECT 1
    FROM flight_pilot AS booked_assignment
    JOIN flight AS booked_flight ON booked_flight.flight_id = booked_assignment.flight_id
    JOIN flight AS target_flight ON target_flight.flight_id = NEW.flight_id
    WHERE booked_assignment.pilot_id = NEW.pilot_id
      AND booked_assignment.flight_id <> NEW.flight_id
      AND NOT (booked_assignment.flight_id = OLD.flight_id
               AND booked_assignment.pilot_id = OLD.pilot_id)
      AND booked_flight.departure_date = target_flight.departure_date
      AND booked_flight.status <> 'Cancelled'
      AND target_flight.status <> 'Cancelled'
)
BEGIN
    SELECT RAISE(ABORT, 'Pilot is already assigned to a flight on that date');
END;

-- Moving a flight's date, or reinstating a cancelled flight
CREATE TRIGGER flight_prevent_double_booking_update
BEFORE UPDATE OF departure_date, status ON flight
WHEN NEW.status <> 'Cancelled'
 AND EXISTS (
    SELECT 1
    FROM flight_pilot AS this_assignment
    JOIN flight_pilot AS other_assignment
      ON other_assignment.pilot_id = this_assignment.pilot_id
     AND other_assignment.flight_id <> this_assignment.flight_id
    JOIN flight AS other_flight ON other_flight.flight_id = other_assignment.flight_id
    WHERE this_assignment.flight_id = NEW.flight_id
      AND other_flight.departure_date = NEW.departure_date
      AND other_flight.status <> 'Cancelled'
)
BEGIN
    SELECT RAISE(ABORT, 'A pilot on this flight is already assigned to a flight on that date');
END;
"""

SEED_SQL = """
-- DESTINATIONS

INSERT INTO destination (destination_id, destination_name, destination_code, planet, region, hazard_level) VALUES
(1,  'Arrakeen',         'ARR', 'Arrakis',         'Northern Basin',     3),
(2,  'Carthag',          'CAR', 'Arrakis',         'Northern Basin',     3),
(3,  'Wind Pass',        'WPS', 'Arrakis',         'Shield Wall',        3),
(4,  'Caladan City',     'CAL', 'Caladan',         'Northern Coast',     1),
(5,  'Salusa Outpost',   'SAL', 'Salusa Secundus', 'Imperial Territory', 5),
(6,  'Kaitain Imperial', 'KAI', 'Kaitain',         'Central Continent',  1),
(7,  'Giedi Port',       'GPR', 'Giedi Prime',     'Industrial Belt',    2),
(8,  'Ix Central',       'IXA', 'Ix',              'Northern District',  1),
(9,  'Tupile Sanctuary', 'TUP', 'Tupile',          'Eastern Province',   1),
(10, 'Vorduun',          'VOR', 'Caladan',         'Western Islands',    1),
(11, 'Qanat Ridge',      'QAN', 'Arrakis',         'Eastern Desert',     4);


-- PILOTS

INSERT INTO pilot (pilot_id, first_name, last_name, licence_class, years_experience, specialisation, call_sign) VALUES
(1,  'Tarek',  'Venn',   'A', 18, 'Long-Haul',            'Sandhawk'),
(2,  'Mara',   'Kynes',  'A', 14, 'Desert Operations',    'Dustwind'),
(3,  'Jalen',  'Corrin', 'B', 11, 'Passenger Transport',  'Falcon'),
(4,  'Soraya', 'Fen',    'A',  9, 'Diplomatic Transport', 'Sirocco'),
(5,  'Rian',   'Vale',   'B',  8, 'Cargo',                'Hauler'),
(6,  'Nadia',  'Sorel',  'A', 16, 'Long-Haul',            'Voyager'),
(7,  'Kieran', 'Holt',   'B',  6, 'Heavy Transport',      'Ironwing'),
(8,  'Lysa',   'Renn',   'B',  5, 'Passenger Transport',  'Swift'),
(9,  'Daro',   'Venn',   'C',  4, 'Desert Operations',    'Mirage'),
(10, 'Amira',  'Tabr',   'A', 12, 'Diplomatic Transport', 'Comet'),
(11, 'Cael',   'Orr',    'C',  3, 'Cargo',                'Freighter'),
(12, 'Elian',  'Harq',   'B',  7, 'Emergency Operations', 'Lifeline');


-- FLIGHTS

INSERT INTO flight (flight_id, flight_number, departure_destination_id, arrival_destination_id, departure_date, departure_time, status, aircraft_type, flight_type) VALUES
(1,  'IA101', 1,  6, '2026-09-01', '08:30', 'Completed', 'Frigate',         'Passenger'),
(2,  'IA102', 6,  1, '2026-09-02', '14:00', 'Completed', 'Frigate',         'Passenger'),
(3,  'IA103', 1,  2, '2026-09-03', '09:15', 'Completed', 'Ornithopter',     'Passenger'),
(4,  'IA104', 2,  1, '2026-09-03', '16:45', 'Completed', 'Ornithopter',     'Passenger'),
(5,  'IA105', 4, 10, '2026-09-04', '15:30', 'Cancelled', 'Ornithopter',     'Cargo'),
(6,  'IA106', 6,  7, '2026-09-02', '13:00', 'Completed', 'Heavy Freighter', 'Cargo'),
(7,  'IA107', 1,  4, '2027-02-01', '07:45', 'Scheduled', 'Frigate',         'Passenger'),
(8,  'IA108', 4,  1, '2027-02-02', '11:30', 'Cancelled', 'Frigate',         'Passenger'),
(9,  'IA109', 8,  6, '2027-02-03', '17:15', 'Scheduled', 'Frigate',         'Passenger'),
(10, 'IA110', 1,  3, '2027-02-01', '06:30', 'Delayed',   'Ornithopter',     'Passenger'),
(11, 'IA111', 6,  5, '2027-02-05', '12:00', 'Scheduled', 'Frigate',         'Diplomatic'),
(12, 'IA112', 5,  6, '2027-02-06', '18:30', 'Delayed',   'Frigate',         'Diplomatic'),
(13, 'IA113', 1, 11, '2027-02-07', '08:00', 'Scheduled', 'Ornithopter',     'Passenger');


-- FLIGHT PILOT ASSIGNMENTS

INSERT INTO flight_pilot (flight_id, pilot_id, role) VALUES
(1,  1,  'Captain'),
(1,  3,  'First Officer'),
(2,  6,  'Captain'),
(3,  2,  'Captain'),
(4,  12, 'Captain'),
(5,  5,  'Captain'),
(6,  7,  'Captain'),
(7,  6,  'Captain'),
(8,  6,  'Captain'),
(9,  8,  'Captain'),
(10, 9,  'Captain'),
(11, 4,  'Captain'),
(11, 10, 'First Officer'),
(12, 10, 'Captain'),
(12, 4,  'First Officer');
"""


def create_schema(conn):
    """Create the tables, indexes and triggers."""
    conn.executescript(SCHEMA_SQL)


def seed(conn):
    """Insert the sample data."""
    conn.executescript(SEED_SQL)


def rebuild(conn):
    """Drop every table and rebuild from the sample data."""
    conn.executescript(DROP_SQL)
    create_schema(conn)
    seed(conn)
    conn.commit()


def build_database(db_path=DEFAULT_DB_PATH, reset=False):
    """Create and seed the database file."""
    if db_path.exists():
        if not reset:
            return False
        db_path.unlink()

    conn = connect(db_path)
    try:
        create_schema(conn)
        seed(conn)
        conn.commit()
    finally:
        conn.close()
    return True


def main():
    """Build the database from the command line."""
    parser = argparse.ArgumentParser(description="Build the flight management database.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="delete the existing database file and rebuild it from scratch",
    )
    args = parser.parse_args()

    built = build_database(reset=args.reset)
    if built:
        print(f"Database built at {DEFAULT_DB_PATH}")
    else:
        print(f"Database already exists at {DEFAULT_DB_PATH}. Use --reset to rebuild it.")


if __name__ == "__main__":
    main()
