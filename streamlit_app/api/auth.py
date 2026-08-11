from api import client


def register_student(
    name: str, email: str, password: str, dob: str, phone: str | None = None
) -> dict:
    """
    dob must be an ISO date string, e.g. '2005-12-31'.
    Returns {"access_token": ..., "token_type": "bearer"}.
    """
    payload = {"name": name, "email": email, "password": password, "dob": dob}
    if phone:
        payload["phone"] = phone
    return client.post("/auth/student/register", json=payload)


def login_student(email: str, password: str) -> dict:
    return client.post(
        "/auth/student/login", json={"email": email, "password": password}
    )


def login_officer(email: str, password: str) -> dict:
    return client.post(
        "/auth/officer/login", json={"email": email, "password": password}
    )
