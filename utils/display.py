"""Printing helpers for query results."""

# Column widths are set by the heading when it is longer than every value.
SHORT_HEADINGS = {
    "flight_id": "ID",
    "flight_number": "Flight",
    "departure": "From",
    "arrival": "To",
    "departure_date": "Date",
    "departure_time": "Time",
    "aircraft_type": "Aircraft",
    "flight_type": "Type",
    "destination_id": "ID",
    "destination_code": "Code",
    "destination_name": "Destination",
    "hazard_level": "Hazard",
    "hazard_label": "Rating",
    "pilot_id": "ID",
    "pilot_name": "Pilot",
    "first_name": "First",
    "last_name": "Surname",
    "licence_class": "Licence",
    "years_experience": "Years",
    "flight_count": "Flights",
    "total_flights": "Total",
    "as_captain": "Captain",
    "as_first_officer": "First Officer",
}


def _heading(field):
    return field.replace("_", " ").title()


def _short_heading(field):
    return SHORT_HEADINGS.get(field) or _heading(field)


def _cell(value):
    return "-" if value is None else str(value)


def _line(values, widths):
    return "  ".join(value.ljust(widths[i]) for i, value in enumerate(values)).rstrip()


def print_table(rows):
    """Print rows as an aligned table."""
    if not rows:
        print("No results.")
        return

    headings = [_short_heading(field) for field in rows[0]._fields]
    cells = [[_cell(value) for value in row] for row in rows]
    widths = [
        max(len(value) for value in column)
        for column in zip(headings, *cells, strict=True)
    ]

    print(_line(headings, widths))
    print("  ".join("-" * width for width in widths))
    for row in cells:
        print(_line(row, widths))
    print(f"\n{len(rows)} row(s).")


def print_record(record):
    """Print one row as a list of fields, for a detailed view."""
    headings = [_heading(field) for field in record._fields]
    width = max(len(heading) for heading in headings)
    for heading, value in zip(headings, record, strict=True):
        print(f"{heading.ljust(width)} : {_cell(value)}")
