"""Super Admin interface for creating employee accounts."""

import streamlit as st

from components.auth_ui import account_role, require_authentication
from services.auth_service import create_user, delete_user, list_users
from services.django_api import ApiError
from services.session_service import token, user
from services.template_client import list_admin_templates


require_authentication()
if not (user() or {}).get("is_superuser"):
    st.error("Super Admin access is required.")
    st.stop()

st.title("Manage Users")
st.caption(
    "Create employee accounts, review access groups, and remove former users."
)

notice = st.session_state.pop("user-admin-notice", None)
if notice:
    st.success(notice)

try:
    templates = list_admin_templates(token())
except ApiError as exc:
    st.error(str(exc))
    st.stop()

suggested_groups = sorted(
    {
        group
        for template_item in templates
        for group in template_item.get("allowed_groups", [])
    }
)
if suggested_groups:
    st.caption(f"Available template groups: {', '.join(suggested_groups)}")

with st.form("super-admin-create-user"):
    username = st.text_input("Username")
    email = st.text_input("Email address")
    first_name, last_name = st.columns(2)
    with first_name:
        given_name = st.text_input("First name")
    with last_name:
        family_name = st.text_input("Last name")
    groups_text = st.text_input(
        "Access groups",
        value="sales" if "sales" in suggested_groups else "",
        help="Comma-separated group names, for example: sales, admin",
    )
    password = st.text_input(
        "Temporary password",
        type="password",
        help="Use at least 8 characters and share it securely with the employee.",
    )
    confirm_password = st.text_input("Confirm password", type="password")
    submitted = st.form_submit_button(
        "Create user",
        type="primary",
        use_container_width=True,
    )

if submitted:
    if password != confirm_password:
        st.error("The passwords do not match.")
        st.stop()

    groups = [group.strip() for group in groups_text.split(",") if group.strip()]
    if not groups:
        st.error("Assign at least one access group.")
        st.stop()

    try:
        created_user = create_user(
            token(),
            {
                "username": username.strip(),
                "email": email.strip(),
                "first_name": given_name.strip(),
                "last_name": family_name.strip(),
                "password": password,
                "groups": groups,
            },
        )
    except ApiError as exc:
        st.error(str(exc))
    else:
        st.success(
            f"User {created_user['username']} was created successfully with "
            f"access to: {', '.join(created_user['groups'])}."
        )

st.divider()
st.subheader("Existing users")

try:
    users = list_users(token())
except ApiError as exc:
    st.error(str(exc))
    st.stop()

current_user_id = (user() or {}).get("id")
for account in users:
    protected = account.get("is_superuser") or account["id"] == current_user_id
    with st.container(border=True):
        details, action = st.columns([3, 2], vertical_alignment="center")
        with details:
            full_name = (
                f"{account.get('first_name', '')} {account.get('last_name', '')}".strip()
            )
            st.markdown(f"#### {full_name or account['username']}")
            st.caption(f"{account['username']} · {account.get('email') or 'No email'}")
            groups = account.get("groups", [])
            st.caption(
                f"{account_role(account)} · Groups: "
                f"{', '.join(groups) if groups else 'None'}"
            )
        with action:
            confirmation = st.checkbox(
                "Confirm deletion",
                key=f"confirm-delete-user-{account['id']}",
                disabled=protected,
                help=(
                    "The current Super Admin account is protected."
                    if protected
                    else "This permanently deletes the user account."
                ),
            )
            if st.button(
                "Delete user",
                key=f"delete-user-{account['id']}",
                disabled=protected or not confirmation,
                use_container_width=True,
            ):
                try:
                    delete_user(token(), account["id"])
                except ApiError as exc:
                    st.error(str(exc))
                else:
                    st.session_state["user-admin-notice"] = (
                        f"User {account['username']} was deleted."
                    )
                    st.rerun()
