"""Reusable template-card UI component."""

import streamlit as st


def render_template_card(template: dict) -> bool:
    """Render one compact template row and return True when opened."""
    with st.container(border=True):
        details, action = st.columns([5, 1.3], vertical_alignment="center")
        with details:
            st.markdown(f"#### {template['name']}")
            st.caption(template.get("description") or "Approved email template")

            field_count = template.get("field_count", 0)
            groups = template.get("allowed_groups", [])
            access_label = ", ".join(groups) if groups else "All authorized users"
            st.caption(f"{field_count} editable text fields · Access: {access_label}")

        with action:
            return st.button(
                "Open template",
                key=f"open-template-{template['id']}",
                type="primary",
                use_container_width=True,
            )

