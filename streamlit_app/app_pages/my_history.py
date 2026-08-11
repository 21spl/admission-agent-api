import streamlit as st
from api import application_history as history_api
from api.client import APIError
from components.auth_guard import require_student

require_student()

st.title("🕓 My Application History")

try:
    history = history_api.get_my_history()
except APIError as e:
    st.error(f"Could not load your history: {e.detail}")
    st.stop()

if not history:
    st.info("No status changes recorded yet.")
else:
    history = sorted(history, key=lambda h: h["changed_at"])
    for entry in history:
        old = entry.get("old_status") or "—"
        st.write(f"**{entry['changed_at']}** — {old} → **{entry['new_status']}**")
