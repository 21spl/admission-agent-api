import pytest

@pytest.mark.asyncio
async def test_app_boots_and_swagger_docs_respond(client):
    response = await client.get("/docs")
    assert response.status_code == 200