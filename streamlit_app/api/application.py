from api import client
from api.client import APIError


def submit_application(total_marks: float, preferences: list[dict]) -> dict:
    """
    preferences: list of {"branch_id": "<uuid>", "preference_order": 1..5}
    """
    payload = {"total_marks": total_marks, "preferences": preferences}
    return client.post("/applications", json=payload)


def get_my_application() -> dict | None:
    """Returns None if the student has no application yet, instead of raising."""
    try:
        return client.get("/applications/me")
    except APIError as e:
        if e.status_code == 404:
            return None
        raise
