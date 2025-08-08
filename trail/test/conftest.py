import os
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient, Request, Response

os.environ["ENV_STATE"] = "test"


from trail.database import database, user_table
from trail.main import app
from trail.test.routers.test_post import create_post


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture()
def client() -> Generator:
    yield TestClient(app)


@pytest.fixture(autouse=True)
async def db() -> AsyncGenerator:
    await database.connect()
    yield database
    await database.disconnect()


@pytest.fixture()
async def async_client(client) -> AsyncGenerator:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=client.base_url
    ) as ac:
        yield ac


@pytest.fixture()
async def registered_user(async_client: AsyncClient):
    user_details = {"email": "test@email.com", "password": "1234"}
    await async_client.post("/register", json=user_details)
    query = user_table.select().where(user_table.c.email == user_details["email"])
    user = await database.fetch_one(query)
    user_details["id"] = user.id
    return user_details


@pytest.fixture()
async def confirmed_user(registered_user: dict) -> dict:
    query = (
        user_table.update()
        .where(user_table.c.email == registered_user["email"])
        .values(confirmed=True)
    )

    await database.execute(query)

    return registered_user


@pytest.fixture()
async def logged_in_token(async_client: AsyncClient, confirmed_user: dict):
    response = await async_client.post("/token", json=confirmed_user)
    return response.json()["access_token"]


@pytest.fixture(autouse=True)
async def mock_httpx_client(mocker):
    mocked_client = mocker.patch("trail.tasks.httpx.AsyncClient")
    mocked_async_client = Mock()
    response = Response(status_code=200, content="", request=Request("Post", "//"))
    mocked_async_client.post = AsyncMock(return_value=response)
    mocked_client.return_value.__aenter__.return_value = mocked_async_client
    return mocked_async_client


@pytest.fixture()
async def created_post(async_client: AsyncClient, logged_in_token: str):
    return await create_post("test post", async_client, logged_in_token)
