from api import client


def get_my_history() -> list[dict]:
    return client.get("/applications/history/me")


def get_history_for_application(application_id: str) -> list[dict]:
    return client.get(f"/applications/history/application/{application_id}")
