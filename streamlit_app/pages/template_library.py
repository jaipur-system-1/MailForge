"""Authorized template library page."""

import streamlit as st

from components.auth_ui import require_authentication
from components.template_card import render_template_card
from services.django_api import ApiError
from services.session_service import token
from services.template_client import list_templates
from services.template_session import select_template


require_authentication()
st.title("Template Library")
st.caption("Choose an approved template and prepare it for a recipient company.")

try:
    templates = list_templates(token())
except ApiError as exc:
    st.error(str(exc))
    st.stop()

search = st.text_input(
    "Search templates",
    placeholder="Search by name or description",
    label_visibility="collapsed",
)

query = search.strip().lower()
if query:
    templates = [
        template
        for template in templates
        if query in template.get("name", "").lower()
        or query in template.get("description", "").lower()
    ]

if not templates:
    if query:
        st.info("No templates match your search.")
    else:
        st.info("No templates are available for your account.")
    st.stop()

st.caption(f"{len(templates)} template{'s' if len(templates) != 1 else ''} available")

for template in templates:
    if render_template_card(template):
        select_template(template)
        st.switch_page("pages/edit_email.py")

