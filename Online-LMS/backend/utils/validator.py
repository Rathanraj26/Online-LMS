"""
validator.py
Simple, dependency-free input validation helpers used by the route layer.
"""
import re

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def is_valid_email(email: str) -> bool:
    return bool(email) and bool(EMAIL_REGEX.match(email))


def is_valid_password(password: str) -> bool:
    """At least 6 characters. Extend with complexity rules as needed."""
    return bool(password) and len(password) >= 6


def require_fields(data: dict, fields: list) -> list:
    """
    Verify required fields are present and non-empty.
    Returns a list of error strings (empty list == valid).
    """
    errors = []
    for field in fields:
        value = data.get(field) if data else None
        if value is None or (isinstance(value, str) and value.strip() == ""):
            errors.append(f"'{field}' is required")
    return errors


def is_allowed_file(filename: str, allowed_extensions: set) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in allowed_extensions
    )


def sanitize_string(value: str) -> str:
    """Basic sanitation to strip control/whitespace padding. Parameterized
    SQL queries (used throughout) are the real SQL-injection defense; this
    is an additional hygiene layer for stored text."""
    if value is None:
        return value
    return value.strip()
