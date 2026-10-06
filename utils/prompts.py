"""Prompts will keep asking until they get a usable answer."""

from datetime import datetime

DATE_SHAPE = "YYYY-MM-DD"
TIME_SHAPE = "HH:MM"


def _ask(label):
    return input(f"{label}: ").strip()


def keep(answer, current):
    """Return the answer or the current value when the prompt was left blank."""
    return current if answer is None else answer


def prompt_text(label, required=True):
    """Ask for a line of text. Returns None if left blank and not required."""
    while True:
        answer = _ask(label)
        if answer or not required:
            return answer or None
        print("Please enter a value.")


def prompt_int(label, minimum=None, maximum=None, required=True):
    """Ask for a whole number, optionally within a range."""
    while True:
        answer = _ask(label)
        if not answer:
            if not required:
                return None
            print("Please enter a number.")
            continue
        try:
            value = int(answer)
        except ValueError:
            print(f"'{answer}' is not a whole number.")
            continue
        if minimum is not None and value < minimum:
            print(f"Please enter {minimum} or more.")
        elif maximum is not None and value > maximum:
            print(f"Please enter {maximum} or less.")
        else:
            return value


def prompt_id(label, valid_ids, blank_hint="blank to go back"):
    """Ask for an ID from the list just shown."""
    if not valid_ids:
        return None
    while True:
        value = prompt_int(f"{label} ({blank_hint})", required=False)
        if value is None:
            return None
        if value in valid_ids:
            return value
        print("That ID is not in the list above.")


def _print_options(options):
    for number, option in enumerate(options, start=1):
        print(f"  {number}. {option}")


def prompt_optional_choice(label, options, zero_label="Any"):
    """Show numbered options with a zero option, and ask for one."""
    print(f"  0. {zero_label}")
    _print_options(options)
    position = prompt_int(f"{label} (0 to {len(options)})", 0, len(options), required=False)
    if position is None or position == 0:
        return None
    return options[position - 1]


def prompt_choice(label, options):
    """Show numbered options (required)."""
    while True:
        _print_options(options)
        position = prompt_int(f"{label} (1 to {len(options)})", 1, len(options), required=False)
        if position is not None:
            return options[position - 1]
        print("Please pick one of the options.")


def _prompt_datetime(label, noun, pattern, shape, blank_hint, required):
    """Ask for a date or time in the given shape."""
    hint = shape if blank_hint is None else f"{shape}, {blank_hint}"
    while True:
        answer = _ask(f"{label} ({hint})")
        if not answer:
            if not required:
                return None
            print(f"Please enter a {noun} as {shape}.")
            continue
        try:
            datetime.strptime(answer, pattern)
        except ValueError:
            print(f"'{answer}' is not in the format {shape}.")
            continue
        return answer


def prompt_date(label, blank_hint=None, required=True):
    """Ask for an ISO date, as the database stores it."""
    return _prompt_datetime(label, "date", "%Y-%m-%d", DATE_SHAPE, blank_hint, required)


def prompt_time(label, blank_hint=None, required=True):
    """Ask for a 24 hour time, as the database stores it."""
    return _prompt_datetime(label, "time", "%H:%M", TIME_SHAPE, blank_hint, required)


def prompt_yes_no(label):
    """Ask a yes or no question."""
    while True:
        answer = _ask(f"{label} (y/n)").lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please answer y or n.")
