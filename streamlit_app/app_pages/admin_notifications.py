import streamlit as st
from api import notification as notification_api
from api.client import APIError
from components.auth_guard import require_officer

require_officer()

st.title("🔔 Notification Logs")

tab_by_app, tab_by_email = st.tabs(["By Application", "By Recipient Email"])

with tab_by_app:
    application_id = st.text_input("Application ID (UUID)", key="notif_app_id")
    if st.button("Search", key="search_by_app", disabled=not application_id.strip()):
        try:
            logs = notification_api.get_notifications_for_application(
                application_id.strip()
            )
        except APIError as e:
            st.error(f"Failed: {e.detail}")
        else:
            if not logs:
                st.info("No notifications found for this application.")
            for log in sorted(
                logs, key=lambda notification: notification["sent_at"], reverse=True
            ):
                st.write(
                    f"**{log['sent_at']}** — {log['type']} → {log['recipient_email']} ({log['status']})"
                )

with tab_by_email:
    email = st.text_input("Recipient Email", key="notif_email")
    if st.button("Search", key="search_by_email", disabled=not email.strip()):
        try:
            logs = notification_api.get_notifications_by_email(email.strip())
        except APIError as e:
            st.error(f"Failed: {e.detail}")
        else:
            if not logs:
                st.info("No notifications found for this recipient.")
            for log in sorted(
                logs, key=lambda notification: notification["sent_at"], reverse=True
            ):
                st.write(
                    f"**{log['sent_at']}** — {log['type']} (App: `{log.get('application_id') or '—'}`) — {log['status']}"
                )
