import streamlit as st
from api import branch as branch_api
from api import offer as offer_api
from api.client import APIError
from components.auth_guard import require_student
from components.status_badge import status_badge

require_student()

st.title("🎓 My Offers")

try:
    offers = offer_api.get_my_offers()
except APIError as e:
    st.error(f"Could not load your offers: {e.detail}")
    st.stop()

if not offers:
    st.info(
        "You don't have any offers yet. Check back after your application is validated."
    )
    st.stop()

try:
    branches = branch_api.list_branches()
    branch_lookup = {b["id"]: b["name"] for b in branches}
except APIError:
    branch_lookup = {}

# Sort most recent first
offers = sorted(offers, key=lambda o: o["sent_at"], reverse=True)

for offer in offers:
    branch_name = branch_lookup.get(offer["branch_id"], offer["branch_id"])
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### {branch_name}")
            st.caption(f"Round {offer['round_number']}")
        with col2:
            status_badge(offer["status"])

        st.write(f"**Sent:** {offer['sent_at']}")
        st.write(f"**Expires:** {offer['expires_at']}")
        if offer.get("responded_at"):
            st.write(f"**Responded:** {offer['responded_at']}")

        if offer["status"] == "PENDING":
            col_accept, col_reject = st.columns(2)
            with col_accept:
                if st.button(
                    "✅ Accept",
                    key=f"accept_{offer['id']}",
                    type="primary",
                    use_container_width=True,
                ):
                    try:
                        offer_api.respond_to_offer(offer["id"], accept=True)
                        st.success("Offer accepted!")
                        st.rerun()
                    except APIError as e:
                        st.error(f"Failed: {e.detail}")
            with col_reject:
                if st.button(
                    "❌ Reject", key=f"reject_{offer['id']}", use_container_width=True
                ):
                    try:
                        offer_api.respond_to_offer(offer["id"], accept=False)
                        st.warning("Offer rejected.")
                        st.rerun()
                    except APIError as e:
                        st.error(f"Failed: {e.detail}")
