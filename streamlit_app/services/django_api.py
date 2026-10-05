"""HTTP client for the MailForge Django API."""

import os
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv

DEFAULT_API_URL = "http://127.0.0.1:8000"
PROJECT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_DIR / ".env")


class ApiError(RuntimeError):
    pass


def _error_message(value) -> str:
    if isinstance(value, dict):
        return " ".join(
            f"{key.replace('_', ' ').title()}: {_error_message(item)}"
            for key, item in value.items()
        )
    if isinstance(value, list):
        return " ".join(_error_message(item) for item in value)
    return str(value)


def api_url() -> str:
    configured_url = os.getenv("DJANGO_API_URL", DEFAULT_API_URL).strip().rstrip("/")
    if not configured_url.startswith(("http://", "https://")):
        raise ApiError("DJANGO_API_URL must start with http:// or https://.")
    return configured_url


def request_timeout() -> float:
    try:
        timeout = float(os.getenv("DJANGO_API_TIMEOUT_SECONDS", "10"))
    except ValueError as exc:
        raise ApiError("DJANGO_API_TIMEOUT_SECONDS must be a number.") from exc
    if timeout <= 0:
        raise ApiError("DJANGO_API_TIMEOUT_SECONDS must be greater than zero.")
    return timeout


def _loading_message(method: str, path: str) -> str:
    normalized_method = method.upper()
    normalized_path = f"/{path.lstrip('/')}"

    if normalized_path.endswith("/api/auth/login/"):
        return "Signing you in…"
    if normalized_path.endswith("/api/auth/logout/"):
        return "Signing you out…"
    if normalized_path.endswith("/render/"):
        return "Rendering your email…"
    if normalized_path.endswith("/api/history/"):
        return "Loading email history…" if normalized_method == "GET" else "Saving email history…"
    if normalized_method == "GET" and "/api/templates/" in normalized_path:
        return "Loading templates…"
    if normalized_method == "GET" and "/api/auth/admin/users/" in normalized_path:
        return "Loading users…"
    if normalized_method == "DELETE":
        return "Deleting…"
    if normalized_method in {"POST", "PUT", "PATCH"}:
        return "Saving changes…"
    return "Loading…"


def request(method: str, path: str, token: str | None = None, **kwargs):
    headers = dict(kwargs.pop("headers", {}))
    if token:
        headers["Authorization"] = f"Token {token}"

    try:
        with st.spinner(_loading_message(method, path), show_time=True):
            response = requests.request(
                method,
                f"{api_url()}/{path.lstrip('/')}",
                headers=headers,
                timeout=request_timeout(),
                **kwargs,
            )
    except requests.RequestException as exc:
        raise ApiError("Cannot connect to the MailForge server.") from exc

    if response.status_code >= 400:
        try:
            payload = response.json()
            message = payload.get("detail") or payload.get("non_field_errors") or payload
        except ValueError:
            message = "The MailForge server returned an unexpected response."
        raise ApiError(_error_message(message))

    if response.status_code == 204:
        return None
    return response.json()

