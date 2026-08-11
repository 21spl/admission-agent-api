import json

import requests
import streamlit as st

API_BASE_URL = st.secrets["API_BASE_URL"]


def _headers(auth: bool) -> dict:
    headers = {"Content-Type": "application/json"}
    if auth:
        token = st.session_state.get("token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
    return headers


def _stream_sse(url: str, payload: dict, auth: bool):
    """
    Yields (event_type, data_dict) tuples parsed from an SSE stream.
    event_type is one of: token, tool_call, tool_result, agent_switch, done, error
    """
    with requests.post(
        url,
        json=payload,
        headers=_headers(auth),
        stream=True,
        timeout=120,
    ) as response:
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except ValueError:
                detail = response.text
            yield "error", {"message": detail}
            return

        event_type = None
        data_lines = []

        for raw_line in response.iter_lines(decode_unicode=True):
            if raw_line is None:
                continue
            line = raw_line.strip("\r")

            if line == "":
                # blank line = end of one SSE message
                if event_type is not None:
                    data_str = "\n".join(data_lines)
                    try:
                        data = json.loads(data_str) if data_str else {}
                    except json.JSONDecodeError:
                        data = {"raw": data_str}
                    yield event_type, data
                event_type = None
                data_lines = []
                continue

            if line.startswith("event:"):
                event_type = line[len("event:") :].strip()
            elif line.startswith("data:"):
                data_lines.append(line[len("data:") :].strip())


def stream_public_chat(message: str, history: list[dict]):
    url = f"{API_BASE_URL}/support/public/chat/stream"
    payload = {"message": message, "history": history}
    yield from _stream_sse(url, payload, auth=False)


def stream_authenticated_chat(message: str, history: list[dict]):
    url = f"{API_BASE_URL}/support/chat/stream"
    payload = {"message": message, "history": history}
    yield from _stream_sse(url, payload, auth=True)
