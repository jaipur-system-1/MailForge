"""Infer editable field definitions from Jinja placeholders in template HTML."""

import json

from jinja2 import Environment, TemplateSyntaxError, meta


LONG_TEXT_HINTS = {
    "body",
    "closing",
    "content",
    "copy",
    "description",
    "details",
    "message",
    "notes",
    "paragraph",
    "summary",
}


class FieldDetectionError(ValueError):
    pass


def _new_field(name: str) -> dict:
    parts = set(name.lower().split("_"))
    is_long_text = bool(parts & LONG_TEXT_HINTS)
    return {
        "name": name,
        "label": name.replace("_", " ").title(),
        "type": "textarea" if is_long_text else "text",
        "required": True,
        "default": "",
        "max_length": 3000 if is_long_text else 500,
    }


def detect_editable_fields(
    html: str,
    fields_json: str,
    preserve_unreferenced: bool = True,
) -> tuple[list[dict], list[str]]:
    """Build field definitions from HTML variables and reuse existing settings."""
    try:
        parsed = Environment().parse(html)
    except TemplateSyntaxError as exc:
        raise FieldDetectionError(f"Invalid template syntax: {exc.message}") from exc

    try:
        existing_fields = json.loads(fields_json)
    except json.JSONDecodeError as exc:
        raise FieldDetectionError(
            f"Editable fields JSON is invalid at line {exc.lineno}."
        ) from exc
    if not isinstance(existing_fields, list):
        raise FieldDetectionError("Editable fields must be a JSON array.")

    variables = meta.find_undeclared_variables(parsed)
    ordered_variables = sorted(
        variables,
        key=lambda name: (html.find(name) if html.find(name) >= 0 else len(html), name),
    )
    existing_by_name = {
        field.get("name"): field
        for field in existing_fields
        if isinstance(field, dict) and field.get("name")
    }
    added_names = [name for name in ordered_variables if name not in existing_by_name]
    detected_fields = [
        existing_by_name.get(name, _new_field(name))
        for name in ordered_variables
    ]
    if preserve_unreferenced:
        detected_names = set(ordered_variables)
        unreferenced_fields = [
            field
            for field in existing_fields
            if isinstance(field, dict) and field.get("name") not in detected_names
        ]
        detected_fields.extend(unreferenced_fields)
    return detected_fields, added_names
