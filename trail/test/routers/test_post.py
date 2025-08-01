import pytest
from httpx import AsyncClient

from trail import security


async def create_post(
    body: str, async_client: AsyncClient, logged_in_token: str
) -> dict:
    response = await async_client.post(
        "/post",
        json={"body": body},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


async def create_comment(
    body: str, post_id: int, async_client: AsyncClient, logged_in_token: str
) -> dict:
    response = await async_client.post(
        "/comment",
        json={
            "body": body,
            "post_id": post_id,
        },
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


async def create_like(
    post_id: int, async_client: AsyncClient, logged_in_token: str
) -> dict:
    response = await async_client.post(
        "/like",
        json={
            "post_id": post_id,
        },
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


@pytest.fixture()
async def created_post(async_client: AsyncClient, logged_in_token: str):
    return await create_post("test post", async_client, logged_in_token)


@pytest.fixture()
async def created_comment(
    async_client: AsyncClient, created_post, logged_in_token: str
):
    return await create_comment(
        "testComment", created_post["id"], async_client, logged_in_token
    )


# @pytest.fixture() not required as we don't create like every time
# async def created_like(async_client: AsyncClient, created_post,created_comment):
#     return await create_like(created_post["id"],async_client)


@pytest.mark.anyio
async def test_create_post(async_client: AsyncClient, logged_in_token: str):
    body = "testPost"
    response = await async_client.post(
        "/post",
        json={"body": body},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    assert response.status_code == 201
    # assert {"id": 1, "body": body}.items() <= response.json().items()


@pytest.mark.anyio
async def test_create_empty_post(async_client: AsyncClient, logged_in_token: str):
    response = await async_client.post(
        "/post",
        json={},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_get_all_posts(async_client: AsyncClient, created_post: dict):
    response = await async_client.get("/post")

    assert response.status_code == 200
    assert response.json() <= [{**created_post, "likes": 0}]


@pytest.mark.anyio
async def test_create_post_expired_token(
    async_client: AsyncClient, registered_user: dict, mocker
):
    mocker.patch("trail.security.access_token_expire_minutes", return_value=-1)
    token = security.create_access_token(registered_user["email"])
    response = await async_client.post(
        "/post",
        json={"body": "this is test post"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


@pytest.mark.anyio
@pytest.mark.parametrize(
    "sorting, expected_order",
    [
        ("new", [2, 1]),
        ("old", [1, 2]),
    ],
)
async def test_sorting(
    async_client: AsyncClient,
    sorting: str,
    expected_order: list[int],
    logged_in_token: str,
):
    await create_post("Test Post 1", async_client, logged_in_token)
    await create_post("Test Post 2", async_client, logged_in_token)

    response = await async_client.get("/post", params={"sorting": sorting})

    assert response.status_code == 200

    expected_order = expected_order
    data = response.json()
    order = [post["id"] for post in data]

    assert expected_order == order


@pytest.mark.anyio
async def test_sorting_likes(async_client: AsyncClient, logged_in_token: str):
    await create_post("Test Post 1", async_client, logged_in_token)
    await create_post("Test Post 2", async_client, logged_in_token)
    await create_like(2, async_client, logged_in_token)
    await create_like(2, async_client, logged_in_token)
    response = await async_client.get("/post", params={"sorting": "most_likes"})

    assert response.status_code == 200

    expected_order = [2, 1]
    data = response.json()
    order = [post["id"] for post in data]

    assert expected_order == order


@pytest.mark.anyio
async def test_create_comment(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    response = await async_client.post(
        "/comment",
        json={
            "body": "this is Comment",
            "post_id": created_post["id"],
        },
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == 201


@pytest.mark.anyio
async def test_get_comment(
    async_client: AsyncClient,
    created_post: dict,
    created_comment: dict,
):
    response = await async_client.get(f"/post/{created_post['id']}/comments")

    assert response.status_code == 200


@pytest.mark.anyio
async def test_get_post_with_comments(
    async_client: AsyncClient,
    created_post: dict,
    created_comment: dict,
):
    response = await async_client.get(f"/post/{created_post['id']}")

    assert response.status_code == 200


@pytest.mark.anyio
async def test_like(async_client: AsyncClient, created_post: dict, logged_in_token):
    response = await async_client.post(
        "/like",
        json={"post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    assert response.status_code == 201
