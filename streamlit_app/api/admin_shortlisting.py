from api import client


def trigger_shortlisting_round(round_number: int) -> dict:
    return client.post(f"/admin/rounds/{round_number}/shortlist")
