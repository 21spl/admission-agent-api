import streamlit as st


def init_session_state():
    defaults = {
        "token": None,
        "user_type": None,  # "student" or "officer"
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_login(token: str, user_type: str):
    st.session_state["token"] = token
    st.session_state["user_type"] = user_type


def is_logged_in() -> bool:
    return st.session_state.get("token") is not None


def is_student() -> bool:
    return st.session_state.get("user_type") == "student"


def is_officer() -> bool:
    return st.session_state.get("user_type") == "officer"


def logout():
    st.session_state["token"] = None
    st.session_state["user_type"] = None
