"""Super Admin interface for creating and updating locked email templates."""

import json

import streamlit as st

from components.auth_ui import require_authentication
from services.django_api import ApiError
from services.field_detection import FieldDetectionError, detect_editable_fields
from services.session_service import token, user
from services.template_client import (
    create_admin_template,
    delete_admin_template,
    get_admin_template,
    list_admin_templates,
    update_admin_template,
)


require_authentication()
if not (user() or {}).get("is_superuser"):
    st.error("Super Admin access is required.")
    st.stop()

st.title("Create / Edit Templates")
st.caption("Create or update locked email templates. Changes become available immediately.")
st.warning(
    "Template HTML is trusted source code. Preview and test every change before employees use it."
)

notice = st.session_state.pop("template-admin-notice", None)
if notice:
    st.success(notice)

try:
    templates = list_admin_templates(token())
except ApiError as exc:
    st.error(str(exc))
    st.stop()

mode = st.segmented_control(
    "Action",
    options=["Edit template", "Create template"],
    default="Edit template" if templates else "Create template",
    width="stretch",
)

is_editing = mode == "Edit template"
template = None

if is_editing:
    if not templates:
        st.info("No templates exist yet. Choose Create template.")
        st.stop()

    template_ids = [item["id"] for item in templates]
    labels = {
        item["id"]: f"{item['name']} ({'Active' if item['active'] else 'Inactive'})"
        for item in templates
    }
    selected_id = st.selectbox(
        "Template",
        options=template_ids,
        format_func=lambda template_id: labels[template_id],
    )
    try:
        template = get_admin_template(token(), selected_id)
    except ApiError as exc:
        st.error(str(exc))
        st.stop()
else:
    selected_id = "new"

defaults = template or {
    "id": "",
    "name": "",
    "description": "",
    "allowed_groups": ["sales"],
    "active": True,
    "fields": [
        {
            "name": "recipient_greeting",
            "label": "Greeting",
            "type": "text",
            "required": True,
            "default": "Dear Team,",
            "max_length": 250,
        }
    ],
    "html": "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n  <meta charset=\"UTF-8\">\n  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n  <title>Email</title>\n</head>\n<body>\n  <p>{{ recipient_greeting }}</p>\n</body>\n</html>\n",
}

editor_key = f"super-admin-template-{selected_id}"
html_key = f"{editor_key}-html"
fields_key = f"{editor_key}-fields"
detection_key = f"{editor_key}-detection"

st.session_state.setdefault(html_key, defaults["html"])
st.session_state.setdefault(
    fields_key,
    json.dumps(defaults["fields"], indent=2, ensure_ascii=False),
)


def detect_fields_from_html() -> None:
    pasted_html = st.session_state[html_key]

    # Cloning an existing template must also clone helper fields that may not
    # appear directly as Jinja placeholders in its HTML (for example the GMC
    # company_name field used to generate the greeting and closing text).
    if not is_editing:
        normalized_html = pasted_html.replace("\r\n", "\n").strip()
        for item in templates:
            try:
                existing_template = get_admin_template(token(), item["id"])
            except ApiError:
                continue
            existing_html = existing_template["html"].replace("\r\n", "\n").strip()
            if existing_html == normalized_html:
                st.session_state[fields_key] = json.dumps(
                    existing_template["fields"],
                    indent=2,
                    ensure_ascii=False,
                )
                st.session_state[detection_key] = (
                    "success",
                    f"Copied all editable fields from {existing_template['name']}.",
                )
                return

    try:
        detected_fields, added_names = detect_editable_fields(
            pasted_html,
            st.session_state[fields_key],
            preserve_unreferenced=is_editing,
        )
    except FieldDetectionError as exc:
        st.session_state[detection_key] = ("error", str(exc))
        return

    st.session_state[fields_key] = json.dumps(
        detected_fields,
        indent=2,
        ensure_ascii=False,
    )
    if added_names:
        st.session_state[detection_key] = (
            "success",
            f"Added editable fields: {', '.join(added_names)}.",
        )
    else:
        st.session_state[detection_key] = (
            "info",
            "All HTML placeholders are already defined as editable fields.",
        )


template_id = st.text_input(
    "Template ID",
    value=defaults["id"],
    disabled=is_editing,
    key=f"{editor_key}-id",
    help="Lowercase letters, numbers, hyphens, and underscores only. Cannot be changed later.",
)
name = st.text_input(
    "Template name",
    value=defaults["name"],
    key=f"{editor_key}-name",
)
description = st.text_input(
    "Description",
    value=defaults.get("description", ""),
    key=f"{editor_key}-description",
)
allowed_groups = st.text_input(
    "Allowed groups",
    value=", ".join(defaults.get("allowed_groups", [])),
    key=f"{editor_key}-groups",
    help="Comma-separated Django group names. Leave blank for all authenticated users.",
)
active = st.checkbox(
    "Active",
    value=defaults.get("active", True),
    key=f"{editor_key}-active",
)
html = st.text_area(
    "Template HTML",
    height=600,
    key=html_key,
    on_change=detect_fields_from_html,
    help=(
        "Paste complete HTML containing Jinja placeholders such as "
        "{{ recipient_greeting }}. Click outside the editor to detect fields."
    ),
)

detection = st.session_state.get(detection_key)
if detection:
    message_type, message = detection
    getattr(st, message_type)(message)

fields_json = st.text_area(
    "Editable fields (automatically detected)",
    height=300,
    key=fields_key,
    help=(
        "Detected placeholders are added automatically. Existing definitions are "
        "preserved and can be adjusted manually."
    ),
)
submitted = st.button(
    "Update template" if is_editing else "Create template",
    type="primary",
    use_container_width=True,
    key=f"{editor_key}-submit",
)

if submitted:
    try:
        fields = json.loads(fields_json)
    except json.JSONDecodeError as exc:
        st.error(f"Editable fields JSON is invalid: {exc.msg} at line {exc.lineno}.")
        st.stop()

    if not isinstance(fields, list):
        st.error("Editable fields must be a JSON array.")
        st.stop()

    payload = {
        "id": template_id.strip(),
        "name": name.strip(),
        "description": description.strip(),
        "allowed_groups": [
            group.strip() for group in allowed_groups.split(",") if group.strip()
        ],
        "active": active,
        "fields": fields,
        "html": html,
    }

    try:
        if is_editing:
            update_admin_template(token(), selected_id, payload)
            st.success("Template updated successfully.")
        else:
            create_admin_template(token(), payload)
            st.success("Template created successfully.")
    except ApiError as exc:
        st.error(str(exc))

if is_editing:
    st.divider()
    st.subheader("Delete template")
    st.caption(
        "Deleting removes the template from MailForge. Its files are archived locally "
        "so they can be recovered if necessary."
    )
    confirm_delete = st.checkbox(
        f"I confirm that I want to delete {template['name']}",
        key=f"confirm-delete-template-{selected_id}",
    )
    if st.button(
        "Delete template",
        key=f"delete-template-{selected_id}",
        disabled=not confirm_delete,
        use_container_width=True,
    ):
        try:
            delete_admin_template(token(), selected_id)
        except ApiError as exc:
            st.error(str(exc))
        else:
            st.session_state["template-admin-notice"] = (
                f"Template {template['name']} was deleted and archived."
            )
            st.rerun()
