from api import client


def list_pending_reviews() -> list[dict]:
    return client.get("/admin/document-reviews/")


def submit_review_decision(application_id: str, approve: bool) -> dict:
    return client.post(
        f"/admin/document-reviews/{application_id}/decision", json={"approve": approve}
    )
