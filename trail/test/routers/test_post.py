import pytest
from httpx import AsyncClient


async def create_post(body: str, async_client: AsyncClient) -> dict:
    response = await async_client.post("/post", json={"body": body})
    return response.json()


async def create_comment(body: str, post_id: int, async_client: AsyncClient) -> dict:
    response = await async_client.post(
        "/comment", json={"body": body, "post_id": post_id}
    )
    return response.json()


async def create_like(post_id: int, async_client: AsyncClient) -> dict:
    response = await async_client.post(
        "/like",
        json={
            "post_id": post_id,
        },
    )
    return response.json()


@pytest.fixture()
async def created_post(async_client: AsyncClient):
    return await create_post("test post", async_client)


@pytest.fixture()
async def created_comment(async_client: AsyncClient, created_post):
    return await create_comment("testComment", created_post["id"], async_client)


# @pytest.fixture() not required as we don't create like every time
# async def created_like(async_client: AsyncClient, created_post,created_comment):
#     return await create_like(created_post["id"],async_client)


@pytest.mark.anyio
async def test_create_post(async_client: AsyncClient):
    body = "testPost"
    response = await async_client.post("/post", json={"body": body})

    assert response.status_code == 201
    # assert {"id": 1, "body": body}.items() <= response.json().items()


@pytest.mark.anyio
async def test_create_empty_post(async_client: AsyncClient):
    response = await async_client.post("/post", json={})

    assert response.status_code == 422


@pytest.mark.anyio
async def test_get_all_posts(async_client: AsyncClient, created_post: dict):
    response = await async_client.get("/post")

    assert response.status_code == 200
    assert response.json() <= [{**created_post, "likes": 0}]


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
):
    await create_post("Test Post 1", async_client)
    await create_post("Test Post 2", async_client)

    response = await async_client.get("/post", params={"sorting": sorting})

    assert response.status_code == 200

    expected_order = expected_order
    data = response.json()
    order = [post["id"] for post in data]

    assert expected_order == order


@pytest.mark.anyio
async def test_sorting_likes(
    async_client: AsyncClient,
):
    await create_post("Test Post 1", async_client)
    await create_post("Test Post 2", async_client)
    await create_like(2, async_client)
    await create_like(2, async_client)
    response = await async_client.get("/post", params={"sorting": "most_likes"})

    assert response.status_code == 200

    expected_order = [2, 1]
    data = response.json()
    order = [post["id"] for post in data]

    assert expected_order == order


@pytest.mark.anyio
async def test_create_comment(async_client: AsyncClient, created_post: dict):
    response = await async_client.post(
        "/comment",
        json={
            "body": "this is Comment",
            "post_id": created_post["id"],
        },
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
async def test_like(async_client: AsyncClient, created_post: dict):
    response = await async_client.post("/like", json={"post_id": created_post["id"]})

    assert response.status_code == 201
