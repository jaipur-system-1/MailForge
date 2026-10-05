"""Session state dedicated to the currently selected email template."""

import streamlit as st

SELECTED_TEMPLATE_KEY = "mailforge_selected_template"


def initialize_template_session() -> None:
    st.session_state.setdefault(SELECTED_TEMPLATE_KEY, None)


def select_template(template: dict) -> None:
    initialize_template_session()
    st.session_state[SELECTED_TEMPLATE_KEY] = template


def selected_template() -> dict | None:
    initialize_template_session()
    return st.session_state.get(SELECTED_TEMPLATE_KEY)
