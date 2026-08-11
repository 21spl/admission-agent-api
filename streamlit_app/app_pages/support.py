import streamlit as st
from api import support as support_api
from utils.session import is_logged_in, is_student

st.title("💬 Support")

use_authenticated = is_logged_in() and is_student()

if is_logged_in() and not is_student():
    st.info(
        "AI support chat is available for students. Officers can use other admin tools."
    )
    st.stop()

if use_authenticated:
    st.caption(
        "You're chatting with the full assistant, which can look up your application, documents, offers, and loan status."
    )
    history_key = "support_history_auth"
else:
    st.caption(
        "You're chatting with our general assistant (public mode). Log in for answers based on your own application."
    )
    history_key = "support_history_public"

if history_key not in st.session_state:
    st.session_state[history_key] = []  # list of {"role": ..., "content": ...}

# --- render past messages ---
for msg in st.session_state[history_key]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- handle new input ---
user_input = st.chat_input("Ask a question...")

if user_input:
    st.session_state[history_key].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    history_payload = st.session_state[history_key][
        :-1
    ]  # exclude the message just sent

    with st.chat_message("assistant"):
        placeholder = st.empty()
        status_placeholder = st.empty()
        accumulated = ""

        stream_fn = (
            support_api.stream_authenticated_chat
            if use_authenticated
            else support_api.stream_public_chat
        )

        try:
            for event_type, data in stream_fn(user_input, history_payload):
                if event_type == "agent_switch":
                    status_placeholder.caption(f"🔀 Routed to: {data.get('agent')}")
                elif event_type == "tool_call":
                    status_placeholder.caption(f"🔧 Using tool: {data.get('tool')}")
                elif event_type == "tool_result":
                    status_placeholder.caption(f"✅ Tool finished: {data.get('tool')}")
                elif event_type == "token":
                    accumulated += data.get("content", "")
                    placeholder.markdown(accumulated + "▌")
                elif event_type == "done":
                    status_placeholder.empty()
                    placeholder.markdown(accumulated)
                elif event_type == "error":
                    status_placeholder.empty()
                    placeholder.error(data.get("message", "Something went wrong."))
                    accumulated = None
        except Exception as e:
            status_placeholder.empty()
            placeholder.error(f"Connection error: {e}")
            accumulated = None

    if accumulated:
        st.session_state[history_key].append(
            {"role": "assistant", "content": accumulated}
        )
