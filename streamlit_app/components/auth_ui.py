"""Shared authentication UI for protected Streamlit pages."""

from html import escape

import streamlit as st

from services.auth_service import logout
from services.django_api import ApiError
from services.session_service import (
    initialize,
    is_authenticated,
    sign_out,
    token,
    user,
)

def display_name() -> str:
    current_user = user() or {}
    return (
        f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip()
        or current_user.get("username", "User")
    )


def account_role(account: dict | None = None) -> str:
    current_user = account if account is not None else (user() or {})
    if current_user.get("is_superuser"):
        return "Super Admin"
    group_names = {
        str(group).strip().casefold() for group in current_user.get("groups", [])
    }
    if "ceo" in group_names:
        return "CEO"
    return "Employee"


def render_account_sidebar() -> None:
    current_user = user() or {}
    role = account_role(current_user)
    safe_name = escape(display_name())
    with st.sidebar:
        st.markdown(
            f"""
            <div class="mailforge-account-card">
              <div class="mailforge-account-label">SIGNED IN AS</div>
              <div class="mailforge-account-name">{safe_name}</div>
              <div class="mailforge-account-role">{role}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Log out", use_container_width=True, key="mailforge-logout"):
            try:
                logout(token())
            except ApiError:
                # A local logout must still succeed if the API is unavailable.
                pass
            sign_out()
            st.rerun()
        st.markdown(
            """
            <div class="mailforge-sidebar-footer">
              Made with <span>♥</span> by Prateek
            </div>
            """,
            unsafe_allow_html=True,
        )


def require_authentication() -> None:
    initialize()
    if not is_authenticated():
        st.warning("Sign in to access this page.")
        st.stop()
