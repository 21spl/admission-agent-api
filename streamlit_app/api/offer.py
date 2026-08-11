from api import client


def get_my_offers() -> list[dict]:
    return client.get("/offers/me")


def respond_to_offer(offer_id: str, accept: bool) -> dict:
    return client.patch(f"/offers/{offer_id}/respond", json={"accept": accept})
