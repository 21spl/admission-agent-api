import streamlit as st
from api import application_history as history_api
from api.client import APIError
from components.auth_guard import require_officer

require_officer()

st.title("🕓 Application Audit Trail")

application_id = st.text_input("Application ID (UUID)")

if st.button("Look up history", type="primary", disabled=not application_id.strip()):
    try:
        history = history_api.get_history_for_application(application_id.strip())
    except APIError as e:
        st.error(f"Failed: {e.detail}")
    else:
        if not history:
            st.info("No history found for this application.")
        else:
            history = sorted(history, key=lambda h: h["changed_at"])
            for entry in history:
                old = entry.get("old_status") or "—"
                st.write(
                    f"**{entry['changed_at']}** — {old} → **{entry['new_status']}**  (by: {entry.get('changed_by') or 'system'})"
                )
