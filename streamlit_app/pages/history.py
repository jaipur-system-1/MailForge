"""Per-user history of emails confirmed as inserted into Gmail."""

from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from components.auth_ui import require_authentication
from services.django_api import ApiError
from services.history_client import list_email_history
from services.session_service import token


require_authentication()
st.title("Email History")
st.caption(
    "Emails that MailForge confirmed were inserted into Gmail. Gmail sending "
    "itself cannot be verified by MailForge."
)

try:
    history = list_email_history(token())
except ApiError as exc:
    st.error(str(exc))
    st.stop()

if not history:
    st.info("No emails have been inserted into Gmail from this account yet.")
    st.stop()

st.caption(f"{len(history)} entr{'y' if len(history) == 1 else 'ies'}")

for entry in history:
    inserted_at = datetime.fromisoformat(entry["inserted_at"].replace("Z", "+00:00"))
    local_time = inserted_at.astimezone(ZoneInfo("Asia/Kolkata"))
    date_label = local_time.strftime("%d %b %Y, %I:%M %p IST")
    recipient = entry["recipient_company"]
    template_name = entry["template_name"]

    with st.container(border=True):
        heading, status = st.columns([3, 1], vertical_alignment="center")
        with heading:
            st.markdown(f"#### {recipient}")
            st.caption(f"{template_name} · {date_label}")
        with status:
            st.success("Inserted into Gmail")

