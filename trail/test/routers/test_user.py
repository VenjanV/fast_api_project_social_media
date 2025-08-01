import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_token_unregistered(async_client: AsyncClient):
    response = await async_client.post(
        "/token", json={"email": "lakfjdslk@gmail.com", "password": "1234"}
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_token(async_client: AsyncClient, registered_user: dict):
    response = await async_client.post(
        "/token",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 200
