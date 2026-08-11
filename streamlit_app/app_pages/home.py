import streamlit as st

# --- Hero ---
st.title("🎓 Your Admission Journey, Simplified")
st.markdown(
    """
    #### One portal for your entire admission process — from application to offer to loan.
    Apply, track your status in real time, upload documents, respond to offers,
    and get instant answers from our AI assistant — all in one place.
    """
)

col1, col2 = st.columns(2)
with col1:
    st.page_link(
        "app_pages/login.py", label="🔑  Login / Register to get started", icon=None
    )
with col2:
    st.page_link(
        "app_pages/support.py", label="💬  Ask our AI assistant a question", icon=None
    )

st.divider()

# --- How it works ---
st.header("How it works")

steps = [
    ("1️⃣", "Register", "Create your student account in under a minute."),
    ("2️⃣", "Apply", "Submit your marks and rank your branch preferences."),
    (
        "3️⃣",
        "Upload Documents",
        "Upload your marksheet, ID, and income certificate for verification.",
    ),
    (
        "4️⃣",
        "Get Validated",
        "Our AI cross-checks your documents automatically — with manual review as a backup.",
    ),
    (
        "5️⃣",
        "Receive Offers",
        "Get matched to a branch based on merit and seat availability, then accept or reject.",
    ),
    (
        "6️⃣",
        "Apply for a Loan",
        "If you need one, apply directly from your dashboard using your income certificate.",
    ),
]

for emoji, title, desc in steps:
    c1, c2 = st.columns([1, 8])
    with c1:
        st.markdown(f"### {emoji}")
    with c2:
        st.markdown(f"**{title}**")
        st.caption(desc)

st.divider()

# --- Features ---
st.header("Why use this portal")

feat1, feat2, feat3 = st.columns(3)
with feat1:
    st.markdown("### ⚡ Real-time Status")
    st.write(
        "Track every stage of your application — no waiting on emails or phone calls."
    )
with feat2:
    st.markdown("### 🤖 AI-Powered Support")
    st.write(
        "Get instant answers about eligibility, documents, offers, and loans — day or night."
    )
with feat3:
    st.markdown("### 🔒 Secure & Transparent")
    st.write(
        "Your documents are verified through an auditable, automated validation pipeline."
    )

st.divider()

# --- FAQ ---
st.header("Frequently asked questions")

with st.expander("Do I need an account to ask questions?"):
    st.write(
        "No — you can chat with our public AI assistant for general questions about "
        "eligibility, branches, and the admission process without logging in. "
        "Log in for answers based on your own application, documents, and offers."
    )

with st.expander("What documents do I need to upload?"):
    st.write(
        "At minimum, your Class 12 marksheet and ID card, which are validated automatically. "
        "You may also need to upload an income certificate if you're applying for a loan."
    )

with st.expander("How are branch offers decided?"):
    st.write(
        "Offers are generated in rounds based on your total marks, branch preferences (in order), "
        "and seat availability at each branch."
    )

with st.expander("Can I change my branch preferences after submitting?"):
    st.write(
        "Once submitted, applications can't be self-edited from the portal. "
        "Contact support if you need a change reviewed."
    )

st.divider()
st.caption("👈 Use the sidebar to log in, register, or chat with our assistant.")
