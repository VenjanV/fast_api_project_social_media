import pytest

from trail import security


@pytest.mark.anyio
async def test_get_user(confirmed_user: dict):
    user = await security.get_user(confirmed_user["email"])

    assert user.email == confirmed_user["email"]


@pytest.mark.anyio
async def test_current_user(confirmed_user: dict):
    token = security.create_access_token(confirmed_user["email"])
    user = await security.get_current_user(token)
    # assert {
    #     "email": "test@email.com",
    #     "password": "1234",
    # }.items() >= (await security.get_current_user(token).items())
    # # async items can't be done like this so use await before async func
    assert user.email == confirmed_user["email"]
