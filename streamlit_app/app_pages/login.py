import streamlit as st
from api import auth as auth_api
from api.client import APIError
from utils.session import set_login

st.title("🔑 Login / Register")

tab_login, tab_register = st.tabs(["Login", "Register"])

with tab_login:
    st.subheader("Login")
    role = st.radio("I am a", ["Student", "Officer"], horizontal=True, key="login_role")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login", type="primary"):
        if not email or not password:
            st.warning("Please enter both email and password.")
        else:
            try:
                if role == "Student":
                    result = auth_api.login_student(email, password)
                    set_login(result["access_token"], "student")
                else:
                    result = auth_api.login_officer(email, password)
                    set_login(result["access_token"], "officer")
                st.rerun()
            except APIError as e:
                st.error(f"Login failed: {e.detail}")

with tab_register:
    st.subheader("Student Registration")
    name = st.text_input("Full name", key="reg_name")
    reg_email = st.text_input("Email", key="reg_email")
    reg_password = st.text_input("Password", type="password", key="reg_password")
    phone = st.text_input("Phone (optional)", key="reg_phone")
    dob = st.date_input("Date of birth", key="reg_dob")

    if st.button("Create account", type="primary"):
        if not name or not reg_email or not reg_password:
            st.warning("Name, email, and password are required.")
        else:
            try:
                result = auth_api.register_student(
                    name=name,
                    email=reg_email,
                    password=reg_password,
                    dob=dob.isoformat(),
                    phone=phone or None,
                )
                set_login(result["access_token"], "student")
                st.success("Account created! Redirecting...")
                st.rerun()
            except APIError as e:
                st.error(f"Registration failed: {e.detail}")
