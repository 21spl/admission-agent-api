from api import client


def list_branches() -> list[dict]:
    return client.get("/branches")


def get_branch(branch_id: str) -> dict:
    return client.get(f"/branches/{branch_id}")
