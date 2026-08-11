import streamlit as st
from api import admin_shortlisting as shortlisting_api
from api.client import APIError
from components.auth_guard import require_officer

require_officer()

st.title("📋 Run Shortlisting Round")
st.caption("Triggers seat allocation and offer generation for the given round number.")

round_number = st.number_input("Round Number", min_value=1, step=1, value=1)

if st.button("Trigger Shortlisting Round", type="primary"):
    try:
        with st.spinner(f"Running shortlisting for round {round_number}..."):
            result = shortlisting_api.trigger_shortlisting_round(int(round_number))
        st.success(f"Round {round_number} completed.")
        st.json(result)
    except APIError as e:
        st.error(f"Failed: {e.detail}")
