"""Email insertion history API operations."""

from .django_api import request


def list_email_history(token: str) -> list[dict]:
    payload = request("GET", "/api/history/", token=token)
    return payload.get("history", [])


def record_email_history(
    token: str,
    *,
    template_id: str,
    recipient_company: str,
) -> dict:
    return request(
        "POST",
        "/api/history/",
        token=token,
        json={
            "template_id": template_id,
            "recipient_company": recipient_company,
        },
    )

