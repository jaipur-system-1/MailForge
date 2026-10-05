"""MailForge Streamlit application entry point."""

from pathlib import Path

import streamlit as st

from components.brand import LOGO_DATA_URI
from components.auth_ui import (
    display_name,
    render_account_sidebar,
)
from services.auth_service import login
from services.django_api import ApiError
from services.session_service import (
    initialize,
    is_authenticated,
    sign_in,
    user,
)


st.set_page_config(
    page_title="MailForge",
    page_icon=str(Path(__file__).resolve().parent / "assets" / "mailforge-favicon.png"),
    layout="centered",
    initial_sidebar_state="expanded",
)
initialize()


def render_app_styles() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #F7FBFD 0%, #EEF6FA 100%);
            border-right: 1px solid #DCE8EE;
            overflow: hidden !important;
        }
        [data-testid="stSidebarHeader"],
        [data-testid="stSidebarCollapseButton"],
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        [data-testid="stSidebarContent"] {
            position: relative;
            height: 100vh;
            box-sizing: border-box;
            padding-top: 88px;
            padding-bottom: 62px;
            overflow-x: hidden !important;
            overflow-y: hidden !important;
            overscroll-behavior: none;
            scrollbar-width: none;
        }
        [data-testid="stSidebarContent"]::-webkit-scrollbar {
            display: none !important;
            width: 0 !important;
            height: 0 !important;
        }
        [data-testid="stSidebarContent"]
        div:has(.mailforge-sidebar-footer):not([data-testid="stSidebarContent"]) {
            position: static !important;
        }
        [data-testid="stSidebarNav"] {
            padding-top: 0;
        }
        [data-testid="stSidebarContent"]
        [data-testid="stElementContainer"]:has(.mailforge-sidebar-brand) {
            position: absolute !important;
            z-index: 2;
            top: 18px;
            left: 12px;
            right: 12px;
            width: auto !important;
        }
        [data-testid="stSidebarNavLink"] {
            min-height: 39px;
            margin: 2px 10px;
            border-radius: 9px;
            color: #355268;
            transition: background-color .15s ease, color .15s ease;
        }
        [data-testid="stSidebarNavLink"]:hover {
            background: #E3F2F9;
            color: #17324D;
        }
        [data-testid="stSidebarNavLink"][aria-current="page"] {
            background: #D9EFF9;
            color: #176F9C;
            font-weight: 650;
        }
        .mailforge-sidebar-brand {
            display: flex;
            align-items: center;
            gap: 11px;
            padding: 4px 4px 12px;
            margin: 0;
            border-bottom: 1px solid #DCE8EE;
        }
        .mailforge-sidebar-logo {
            display: block;
            width: 38px;
            height: 38px;
            flex: 0 0 38px;
            border-radius: 10px;
            object-fit: contain;
            box-shadow: 0 5px 14px rgba(10, 49, 197, .20);
        }
        .mailforge-sidebar-name {
            color: #17324D;
            font-size: 1.06rem;
            font-weight: 750;
            line-height: 1.25;
        }
        .mailforge-sidebar-tagline {
            margin-top: 2px;
            color: #718793;
            font-size: .72rem;
            line-height: 1.25;
        }
        .mailforge-account-card {
            margin: 10px 4px 7px;
            padding: 10px 13px;
            border: 1px solid #DCE8EE;
            border-radius: 10px;
            background: rgba(255, 255, 255, .72);
        }
        .mailforge-account-label {
            color: #83949D;
            font-size: .63rem;
            font-weight: 700;
            letter-spacing: .08em;
        }
        .mailforge-account-name {
            margin-top: 4px;
            overflow: hidden;
            color: #17324D;
            font-size: .88rem;
            font-weight: 700;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .mailforge-account-role {
            margin-top: 2px;
            color: #279FDA;
            font-size: .72rem;
            font-weight: 600;
        }
        .mailforge-sidebar-footer {
            position: absolute;
            bottom: 12px;
            left: 0;
            right: 0;
            width: auto;
            box-sizing: border-box;
            padding: 0;
            border: 0;
            background: transparent;
            color: #718793;
            font-size: .71rem;
            overflow: hidden;
            pointer-events: none;
            text-align: center;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .mailforge-sidebar-footer span {
            color: #E25555;
        }
        [data-testid="stSidebar"] [data-testid="stButton"] button {
            min-height: 38px;
            border-color: #CADCE5;
            border-radius: 8px;
            background: rgba(255, 255, 255, .74);
            color: #355268;
        }
        [data-testid="stSidebar"] [data-testid="stButton"] button:hover {
            border-color: #279FDA;
            color: #176F9C;
        }
        [data-testid="stMainBlockContainer"] {
            padding-top: 2.4rem;
            padding-bottom: 3rem;
        }
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: #DFE9EE !important;
            border-radius: 11px !important;
            box-shadow: 0 2px 8px rgba(23, 50, 77, .035);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


render_app_styles()


def render_sidebar_brand() -> None:
    with st.sidebar:
        st.markdown(
            f"""
            <div class="mailforge-sidebar-brand">
              <img
                class="mailforge-sidebar-logo"
                src="{LOGO_DATA_URI}"
                alt="MailForge logo"
              >
              <div>
                <div class="mailforge-sidebar-name">MailForge</div>
                <div class="mailforge-sidebar-tagline">Approved email workspace</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_login() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] > .main {
            background: #FFFFFF;
        }
        [data-testid="stMainBlockContainer"] {
            max-width: 360px !important;
            padding: 15vh 16px 32px !important;
        }
        [data-testid="stSidebar"], [data-testid="collapsedControl"] {
            display: none;
        }
        [data-testid="stHeader"], [data-testid="stToolbar"],
        [data-testid="stDecoration"], #MainMenu {
            display: none !important;
        }
        .mailforge-mark {
            display: block;
            width: 62px;
            height: 62px;
            margin: 0 auto .55rem;
            border-radius: 16px;
            object-fit: contain;
            box-shadow: 0 7px 20px rgba(10, 49, 197, .18);
        }
        .mailforge-title {
            text-align: center;
            color: #17324D;
            font-size: 1.35rem;
            font-weight: 700;
            margin-bottom: .1rem;
        }
        .mailforge-caption {
            text-align: center;
            color: #6B7D88;
            font-size: .8rem;
            margin-bottom: .9rem;
        }
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: #E1E8ED !important;
            border-radius: 10px !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"] > div {
            padding: 14px !important;
        }
        [data-testid="stTextInput"] {
            margin-bottom: -.15rem;
        }
        [data-testid="stTextInput"] label p {
            font-size: .82rem !important;
        }
        [data-testid="stTextInput"] input {
            min-height: 40px !important;
            height: 40px !important;
            padding: 0 12px !important;
            font-size: .85rem !important;
        }
        [data-testid="stTextInput"] input::placeholder {
            color: #8A9AA5 !important;
            opacity: 1 !important;
        }
        [data-testid="InputInstructions"] {
            display: none !important;
        }
        [data-testid="stFormSubmitButton"] button {
            min-height: 40px !important;
            height: 40px !important;
            font-size: .86rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<img class="mailforge-mark" src="{LOGO_DATA_URI}" alt="MailForge logo">',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="mailforge-title">MailForge</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="mailforge-caption">Sign in to continue</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        with st.form(
            "login-form",
            clear_on_submit=False,
            enter_to_submit=False,
            border=False,
        ):
            username = st.text_input(
                "Username or email",
                autocomplete="username",
                placeholder="name@company.com",
            )
            password = st.text_input(
                "Password",
                type="password",
                autocomplete="current-password",
                placeholder="Password",
            )
            submitted = st.form_submit_button(
                "Sign in",
                use_container_width=True,
                type="primary",
            )

        if submitted:
            if not username.strip() or not password:
                st.error("Enter your username/email and password.")
                return
            try:
                payload = login(username.strip(), password)
            except ApiError as exc:
                st.error(str(exc))
                return
            sign_in(payload["token"], payload["user"])
            st.rerun()


def render_home() -> None:
    name = display_name()
    current_user = user() or {}
    st.title("MailForge")
    st.success(f"Welcome, {name}.")
    st.caption(
        "Create approved, consistently branded emails and insert them into Gmail."
    )

    st.subheader("User manual")
    st.markdown(
        """
        1. **Open Template Library** and choose an email template available to your account.
        2. On **Prepare Email**, enter the **recipient company name**. MailForge generates the approved email automatically.
        3. Review the complete, read-only email in **Desktop** or **Mobile** view.
        4. Open Gmail in the same Chrome profile and start a new compose window.
        5. Select **Insert into Gmail** in MailForge and wait for the successful-insertion confirmation.
        6. Switch to the Gmail compose window. Make any necessary final text changes there.
        7. Review the recipient, subject, complete email text, links, and attachments before sending.
        8. Return to MailForge and select **Prepare another email** when you are ready for the next recipient.
        9. Open **Email History** to review the template, recipient company, and insertion date.

        MailForge resets the prepared email after Gmail confirms a successful insertion.
        History records confirmed Gmail insertion, not confirmation that Gmail sent the message.
        Logging out also clears unfinished recipient details. If Gmail insertion cannot
        connect, reload the MailForge extension and refresh the MailForge and Gmail tabs once.
        """
    )
    st.page_link(
        "pages/template_library.py",
        label="Open Template Library",
        icon=":material/library_books:",
        use_container_width=True,
    )

    groups = current_user.get("groups", [])
    st.caption(
        "Your access groups: " + (", ".join(groups) if groups else "No groups assigned")
    )

    if current_user.get("is_superuser"):
        st.divider()
        st.subheader("Super Admin manual")
        st.markdown(
            """
            As Super Admin, you can manage the approved template library and employee accounts.

            **Templates**

            - Create a template by adding its name, access groups, complete HTML, and active status.
            - Use simple Jinja placeholders such as `{{ company_name }}` for editable content.
            - After pasting HTML, click outside the editor to detect editable fields automatically.
            - Edit and preview templates carefully before making them available to employees.
            - Template deletion requires confirmation and archives the source for recovery.

            **Users**

            - Create employee accounts and assign groups such as `sales` or `admin`.
            - Review existing users and their access groups.
            - Delete former employee accounts after confirmation.
            - Your Super Admin account is protected and cannot be deleted from MailForge.
            """
        )
        template_admin, user_admin = st.columns(2)
        with template_admin:
            st.page_link(
                "pages/super_admin.py",
                label="Create/Edit Templates",
                icon=":material/edit_document:",
                use_container_width=True,
            )
        with user_admin:
            st.page_link(
                "pages/user_admin.py",
                label="Manage Users",
                icon=":material/manage_accounts:",
                use_container_width=True,
            )


if is_authenticated():
    render_sidebar_brand()
    render_account_sidebar()
    pages = [
        st.Page(render_home, title="Home", icon=":material/home:", default=True),
        st.Page(
            "pages/template_library.py",
            title="Template Library",
            icon=":material/library_books:",
        ),
        st.Page(
            "pages/edit_email.py",
            title="Prepare Email",
            icon=":material/draft:",
        ),
        st.Page(
            "pages/history.py",
            title="Email History",
            icon=":material/history:",
        ),
    ]
    if (user() or {}).get("is_superuser"):
        pages.append(
            st.Page(
                "pages/super_admin.py",
                title="Create/Edit Templates",
                icon=":material/edit_document:",
            )
        )
        pages.append(
            st.Page(
                "pages/user_admin.py",
                title="Manage Users",
                icon=":material/manage_accounts:",
            )
        )
    navigation = st.navigation(pages, position="sidebar", expanded=True)
else:
    navigation = st.navigation(
        [st.Page(render_login, title="Sign in", default=True)],
        position="hidden",
    )

navigation.run()

