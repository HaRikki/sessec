"""Validation of submitted form data against the fields detected on the original page."""
import re
from typing import Any

from backend.services.form_definitions import FORMS

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DEFAULT_MAX = 5000


class FormNotFound(KeyError):
    pass


def clean_submission(slug: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Return the cleaned payload or raise ValueError(list_of_messages)."""
    definition = FORMS.get(slug)
    if definition is None:
        raise FormNotFound(slug)
    errors: list[str] = []
    cleaned: dict[str, Any] = {}
    for field in definition["fields"]:
        name = field["name"]
        value = payload.get(name)
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        value = "" if value is None else str(value).strip()
        label = field.get("label") or name
        if field.get("required") and not value:
            errors.append(f"{label} is required.")
            continue
        if not value:
            continue
        if len(value) > (field.get("maxlength") or DEFAULT_MAX):
            errors.append(f"{label} is too long.")
            continue
        if field["type"] == "email" and not _EMAIL.match(value):
            errors.append(f"{label} must be a valid email address.")
            continue
        if field["type"] == "select" and field.get("options") and value not in field["options"]:
            errors.append(f"{label} has an invalid choice.")
            continue
        cleaned[name] = value
    if errors:
        raise ValueError(errors)
    return cleaned
