import streamlit as st
from utils.constants import DEFAULT_STATUS_COLOR, STATUS_COLORS


def status_badge(status: str):
    """Renders a colored pill badge for any status enum value."""
    text_color, bg_color = STATUS_COLORS.get(status, DEFAULT_STATUS_COLOR)
    label = status.replace("_", " ").title()
    st.markdown(
        f"""
        <span style="
            background-color:{bg_color};
            color:{text_color};
            padding: 4px 12px;
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 600;
            display: inline-block;
        ">{label}</span>
        """,
        unsafe_allow_html=True,
    )
