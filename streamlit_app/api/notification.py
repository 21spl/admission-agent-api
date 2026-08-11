from api import client


def get_notifications_for_application(application_id: str) -> list[dict]:
    return client.get(f"/notifications/application/{application_id}")


def get_notifications_by_email(email: str) -> list[dict]:
    return client.get("/notifications/recipient", params={"email": email})
