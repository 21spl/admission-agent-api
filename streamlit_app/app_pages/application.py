import streamlit as st
from api import application as application_api
from api import branch as branch_api
from api.client import APIError
from components.auth_guard import require_student
from components.status_badge import status_badge

require_student()

st.title("📝 My Application")

try:
    application = application_api.get_my_application()
except APIError as e:
    st.error(f"Could not load your application: {e.detail}")
    st.stop()

if application:
    st.subheader("Current Application")
    status_badge(application["status"])
    st.metric("Total Marks", application["total_marks"])
    st.caption(
        f"Submitted: {application['submitted_at']}  ·  Last updated: {application['updated_at']}"
    )

    try:
        branches = branch_api.list_branches()
        branch_lookup = {b["id"]: b["name"] for b in branches}
    except APIError:
        branch_lookup = {}

    st.markdown("**Branch Preferences**")
    prefs = sorted(application["preferences"], key=lambda p: p["preference_order"])
    for p in prefs:
        branch_name = branch_lookup.get(p["branch_id"], p["branch_id"])
        st.write(f"{p['preference_order']}. {branch_name}")

    st.info(
        "You have already submitted an application. Contact support if you need changes."
    )

else:
    st.subheader("Submit New Application")
    st.caption("Enter your marks and rank up to 5 branch preferences.")

    try:
        branches = branch_api.list_branches()
    except APIError as e:
        st.error(f"Could not load branches: {e.detail}")
        st.stop()

    if not branches:
        st.warning("No branches are available yet. Please check back later.")
        st.stop()

    branch_options = {
        f"{b['name']} ({b['code']}) — {b['available_seats']} seats left": b["id"]
        for b in branches
    }

    with st.form("application_form"):
        total_marks = st.number_input(
            "Total Marks", min_value=0.0, max_value=100.0, step=0.01
        )

        st.markdown("**Branch Preferences** (in order of priority)")
        max_prefs = min(5, len(branch_options))
        num_prefs = st.number_input(
            "How many branches to rank?",
            min_value=1,
            max_value=max_prefs,
            value=1,
            step=1,
        )

        preference_labels = []
        for i in range(int(num_prefs)):
            label = st.selectbox(
                f"Preference {i + 1}",
                options=list(branch_options.keys()),
                key=f"branch_{i}",
            )
            preference_labels.append(label)

        submitted = st.form_submit_button("Submit Application", type="primary")

    if submitted:
        if len(set(preference_labels)) != len(preference_labels):
            st.warning("Each branch preference must be unique.")
        else:
            preferences = [
                {"branch_id": branch_options[label], "preference_order": i + 1}
                for i, label in enumerate(preference_labels)
            ]
            try:
                application_api.submit_application(total_marks, preferences)
                st.success("Application submitted successfully!")
                st.rerun()
            except APIError as e:
                st.error(f"Submission failed: {e.detail}")
