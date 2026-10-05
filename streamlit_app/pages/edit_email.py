"""Recipient details and read-only email preview."""

import re

import streamlit as st

from components.auth_ui import require_authentication
from components.gmail_insert import render_gmail_insert
from services.django_api import ApiError
from services.history_client import record_email_history
from services.session_service import token
from services.template_client import get_template, render_template
from services.template_session import selected_template


require_authentication()
selected = selected_template()

if selected is None:
    st.warning("Select a template from the library first.")
    st.page_link("pages/template_library.py", label="Open Template Library")
    st.stop()

insert_notice = st.session_state.get("mailforge-insert-notice")
if insert_notice:
    st.title("Email inserted into Gmail")
    st.success(insert_notice)
    st.info(
        "Switch to the Gmail compose window now. Review the recipient, subject, "
        "complete email text, links and attachments before sending."
    )
    if st.button(
        "Prepare another email",
        type="primary",
        use_container_width=True,
    ):
        st.session_state.pop("mailforge-insert-notice", None)
        st.rerun()
    st.stop()

try:
    template = get_template(token(), selected["id"])
except ApiError as exc:
    st.error(str(exc))
    st.stop()

st.title(template["name"])
st.caption("Enter the recipient company name, then review the generated email.")

fields_by_name = {field["name"]: field for field in template["fields"]}
company_field = fields_by_name.get("company_name")
draft_key = f"mailforge_recipient_draft_{template['id']}"
input_key = f"recipient_company_{template['id']}"
st.session_state.setdefault(draft_key, "")
st.session_state.setdefault(input_key, st.session_state[draft_key])


def save_recipient() -> None:
    st.session_state[draft_key] = st.session_state[input_key].strip()


def reset_email() -> None:
    st.session_state[draft_key] = ""
    st.session_state[input_key] = ""


back_column, reset_column = st.columns([1, 1])
with back_column:
    if st.button("Back to library", use_container_width=True):
        st.switch_page("pages/template_library.py")
with reset_column:
    st.button("Reset email", use_container_width=True, on_click=reset_email)

if company_field is None:
    st.error("This template does not define a recipient company field.")
    st.stop()

st.text_input(
    "Recipient company name",
    key=input_key,
    max_chars=company_field.get("max_length", 150),
    placeholder="Enter the recipient company",
    on_change=save_recipient,
)
company_name = st.session_state[draft_key].strip()

if not company_name:
    st.info("Enter the recipient company name to generate the email preview.")
    st.stop()


def automatic_greeting(name: str) -> str:
    return f"Dear {name} Team,"


def automatic_closing(name: str) -> str:
    return (
        f"We look forward to the opportunity to work with {name} and support "
        "your organisation with a comprehensive, responsive and professionally "
        "managed Group Medical Insurance programme."
    )


values = {
    field["name"]: field.get("default", "") for field in template["fields"]
}
values["company_name"] = company_name
if "recipient_greeting" in values:
    values["recipient_greeting"] = automatic_greeting(company_name)
if "closing_message" in values:
    values["closing_message"] = automatic_closing(company_name)

try:
    payload = render_template(token(), template["id"], values)
except ApiError as exc:
    st.error(str(exc))
    st.stop()

def reset_after_gmail_insert() -> None:
    try:
        record_email_history(
            token(),
            template_id=template["id"],
            recipient_company=company_name,
        )
    except ApiError as exc:
        notice = (
            "Email inserted into Gmail, but its history entry could not be saved: "
            f"{exc}"
        )
    else:
        notice = (
            "Email inserted into Gmail and added to History. MailForge is ready "
            "for the next recipient."
        )
    reset_email()
    st.session_state["mailforge-insert-notice"] = notice

st.info(
    "You can make final text changes in Gmail. Review the complete email "
    "before sending."
)

download_column, gmail_column = st.columns([1, 2])
with download_column:
    filename_base = re.sub(
        r"[^a-z0-9]+", "-", template["name"].lower()
    ).strip("-")
    st.download_button(
        "Download HTML",
        data=payload["html"],
        file_name=f"{filename_base or 'mailforge-email'}.html",
        mime="text/html",
        use_container_width=True,
        on_click="ignore",
    )
with gmail_column:
    render_gmail_insert(
        payload["html"],
        key=f"gmail_insert_{template['id']}",
        on_inserted=reset_after_gmail_insert,
    )

preview_mode = st.segmented_control(
    "Preview width",
    options=["Desktop", "Mobile"],
    default="Desktop",
    label_visibility="collapsed",
    width="stretch",
)

if preview_mode == "Mobile":
    _, mobile_column, _ = st.columns([0.45, 1, 0.45])
    with mobile_column:
        st.iframe(payload["html"], width="stretch", height=760)
else:
    st.iframe(payload["html"], width="stretch", height=800)
