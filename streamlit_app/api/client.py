import requests
import streamlit as st

API_BASE_URL = st.secrets["API_BASE_URL"]


class APIError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def _headers() -> dict:
    headers = {}
    token = st.session_state.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def request(method: str, endpoint: str, **kwargs) -> dict:
    """
    Core HTTP wrapper. endpoint should start with '/', e.g. '/auth/student/login'.
    Raises APIError on non-2xx responses or connection issues.
    """
    url = f"{API_BASE_URL}{endpoint}"
    headers = kwargs.pop("headers", {})
    headers.update(_headers())

    try:
        response = requests.request(method, url, headers=headers, timeout=30, **kwargs)
    except requests.exceptions.ConnectionError:
        raise APIError(0, "Could not connect to the server. Please try again later.")
    except requests.exceptions.Timeout:
        raise APIError(0, "The request timed out. Please try again.")

    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise APIError(response.status_code, detail)

    if response.status_code == 204 or not response.content:
        return {}
    return response.json()


def get(endpoint: str, **kwargs) -> dict:
    return request("GET", endpoint, **kwargs)


def post(endpoint: str, **kwargs) -> dict:
    return request("POST", endpoint, **kwargs)


def put(endpoint: str, **kwargs) -> dict:
    return request("PUT", endpoint, **kwargs)


def patch(endpoint: str, **kwargs) -> dict:
    return request("PATCH", endpoint, **kwargs)


def delete(endpoint: str, **kwargs) -> dict:
    return request("DELETE", endpoint, **kwargs)
