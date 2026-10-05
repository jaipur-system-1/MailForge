"""Authentication helpers for Streamlit sessions."""

from .django_api import request


def login(username: str, password: str) -> dict:
    return request(
        "POST",
        "/api/auth/login/",
        json={"username": username, "password": password},
    )


def logout(token: str) -> None:
    request("POST", "/api/auth/logout/", token=token)


def create_user(token: str, payload: dict) -> dict:
    return request("POST", "/api/auth/admin/users/", token=token, json=payload)


def list_users(token: str) -> list[dict]:
    payload = request("GET", "/api/auth/admin/users/", token=token)
    return payload.get("users", [])


def delete_user(token: str, user_id: int) -> None:
    request("DELETE", f"/api/auth/admin/users/{user_id}/", token=token)

