"""Safely render approved text values into locked HTML templates."""

from jinja2 import Environment, StrictUndefined, select_autoescape
from markupsafe import Markup, escape


class TemplateRenderError(ValueError):
    pass


def _safe_multiline_text(value: str) -> Markup:
    escaped = escape(value.strip())
    return Markup(str(escaped).replace("\r\n", "\n").replace("\n", "<br>\n"))


def render_template(template: dict, values: dict) -> str:
    fields = template.get("fields", [])
    allowed_names = {field["name"] for field in fields}
    unknown_names = set(values) - allowed_names
    if unknown_names:
        raise TemplateRenderError("Unexpected editable fields were provided.")

    raw_values = {}
    for field in fields:
        name = field["name"]
        value = str(values.get(name, field.get("default", ""))).strip()
        if field.get("required") and not value:
            raise TemplateRenderError(f"{field['label']} is required.")
        if len(value) > field.get("max_length", 5000):
            raise TemplateRenderError(f"{field['label']} is too long.")
        raw_values[name] = value

    value_environment = Environment(
        autoescape=False,
        undefined=StrictUndefined,
    )
    template_environment = Environment(
        autoescape=select_autoescape(default_for_string=True),
        undefined=StrictUndefined,
    )

    resolved_values = {}
    for name, value in raw_values.items():
        try:
            resolved = value_environment.from_string(value).render(**raw_values)
        except Exception as exc:
            raise TemplateRenderError(f"Unable to render {name}.") from exc
        resolved_values[name] = _safe_multiline_text(resolved)

    try:
        return template_environment.from_string(template["html"]).render(**resolved_values)
    except Exception as exc:
        raise TemplateRenderError("Unable to render the email template.") from exc

