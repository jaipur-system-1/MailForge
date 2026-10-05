"""Template API operations used by the Streamlit application."""

from .django_api import request


def list_templates(token: str) -> list[dict]:
    payload = request("GET", "/api/templates/", token=token)
    return payload.get("templates", [])


def get_template(token: str, template_id: str) -> dict:
    return request("GET", f"/api/templates/{template_id}/", token=token)


def render_template(token: str, template_id: str, values: dict) -> dict:
    return request(
        "POST",
        f"/api/templates/{template_id}/render/",
        token=token,
        json={"values": values},
    )


def list_admin_templates(token: str) -> list[dict]:
    payload = request("GET", "/api/templates/admin/", token=token)
    return payload.get("templates", [])


def get_admin_template(token: str, template_id: str) -> dict:
    return request("GET", f"/api/templates/admin/{template_id}/", token=token)


def create_admin_template(token: str, payload: dict) -> dict:
    return request("POST", "/api/templates/admin/", token=token, json=payload)


def update_admin_template(token: str, template_id: str, payload: dict) -> dict:
    return request(
        "PUT",
        f"/api/templates/admin/{template_id}/",
        token=token,
        json=payload,
    )


def delete_admin_template(token: str, template_id: str) -> None:
    request("DELETE", f"/api/templates/admin/{template_id}/", token=token)
