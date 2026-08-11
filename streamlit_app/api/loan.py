from api import client
from api.client import APIError


def apply_for_loan(filename: str, file_bytes: bytes, content_type: str) -> dict:
    files = {"file": (filename, file_bytes, content_type)}
    return client.post("/loan/apply", files=files)


def get_loan_status() -> dict | None:
    """Returns None if the student hasn't applied for a loan yet."""
    try:
        return client.get("/loan/status")
    except APIError as e:
        if e.status_code == 404:
            return None
        raise
