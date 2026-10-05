"""Streamlit session-state helpers."""

import streamlit as st

from .template_session import SELECTED_TEMPLATE_KEY


TOKEN_KEY = "mailforge_auth_token"
USER_KEY = "mailforge_user"


def initialize() -> None:
    st.session_state.setdefault(TOKEN_KEY, None)
    st.session_state.setdefault(USER_KEY, None)
    st.session_state.setdefault(SELECTED_TEMPLATE_KEY, None)


def sign_in(token: str, user: dict) -> None:
    st.session_state[TOKEN_KEY] = token
    st.session_state[USER_KEY] = user


def sign_out() -> None:
    st.session_state[TOKEN_KEY] = None
    st.session_state[USER_KEY] = None
    st.session_state[SELECTED_TEMPLATE_KEY] = None
    st.session_state.pop("mailforge-insert-notice", None)
    draft_prefixes = (
        "mailforge_recipient_draft_",
        "recipient_company_",
    )
    for key in list(st.session_state):
        if key.startswith(draft_prefixes):
            del st.session_state[key]


def is_authenticated() -> bool:
    return bool(st.session_state.get(TOKEN_KEY) and st.session_state.get(USER_KEY))


def token() -> str | None:
    return st.session_state.get(TOKEN_KEY)


def user() -> dict | None:
    return st.session_state.get(USER_KEY)

