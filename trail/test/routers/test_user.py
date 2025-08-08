import logging

import pytest
from fastapi import Request
from httpx import AsyncClient

logger = logging.getLogger(__name__)


async def register_user(async_client: AsyncClient, email: str, password: str):
    return await async_client.post(
        "/register", json={"email": email, "password": password}
    )


@pytest.mark.anyio
async def test_token_unregistered(async_client: AsyncClient):
    response = await async_client.post(
        "/token", json={"email": "lakfjdslk@gmail.com", "password": "1234"}
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_token(async_client: AsyncClient, confirmed_user: dict):
    response = await async_client.post(
        "/token",
        json={
            "email": confirmed_user["email"],
            "password": confirmed_user["password"],
        },
    )
    assert response.status_code == 200


@pytest.mark.anyio
async def test_user_confirmation(async_client: AsyncClient, mocker):
    spy = mocker.spy(Request, "url_for")

    details = await register_user(async_client, "test@gmail.com", "1234")
    logger.info(f"detail is {details}")
    confirmation_url = str(spy.spy_return)
    response = await async_client.get(confirmation_url)

    assert response.status_code == 200


@pytest.mark.anyio
async def test_user_expired_token(async_client: AsyncClient, mocker):
    mocker.patch("trail.security.confirm_token_expire_minutes", return_value=-1)

    spy = mocker.spy(Request, "url_for")

    details = await register_user(async_client, "test@gmail.com", "1234")
    logger.info(f"detail is {details}")
    confirmation_url = str(spy.spy_return)
    response = await async_client.get(confirmation_url)

    assert response.status_code == 401
