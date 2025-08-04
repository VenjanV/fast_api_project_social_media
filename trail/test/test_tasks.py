import httpx
import pytest
from databases import Database

from trail.database import post_table
from trail.tasks import APIResponseError, _generate_cute_image, generate_and_add_to_post


@pytest.mark.anyio
async def test_update_url(mock_httpx_client):
    json_data = "https://www.example.com/image.jpg"
    mock_httpx_client.post.return_value = httpx.Response(
        status_code=200, json=json_data, request=httpx.Request("POST", "//")
    )

    result = await _generate_cute_image("a cat")
    assert result == json_data


@pytest.mark.anyio
async def test_insert_link(mock_httpx_client, created_post: dict, db: Database):
    json_data = {"output_url": "https://www.example.com/image.jpg"}
    mock_httpx_client.post.return_value = httpx.Response(
        status_code=200, json=json_data, request=httpx.Request("POST", "//")
    )

    await generate_and_add_to_post(created_post["id"], "/post/1", db, "A Cat")

    query = post_table.select().where(post_table.c.id == created_post["id"])

    updated_post = await db.fetch_one(query)
    assert updated_post.url_link == json_data["output_url"]


@pytest.mark.anyio
async def test_update_url_error(mock_httpx_client):
    mock_httpx_client.post.return_value = httpx.Response(
        status_code=500, content="", request=httpx.Request("POST", "//")
    )

    with pytest.raises(
        APIResponseError, match="api request failed with status code 500"
    ):
        await _generate_cute_image("A Cat")


@pytest.mark.anyio
async def test_update_url_data_error(mock_httpx_client):
    mock_httpx_client.post.return_value = httpx.Response(
        status_code=200, content="Not Json", request=httpx.Request("POST", "//")
    )

    with pytest.raises(APIResponseError, match="api request parsing failed "):
        await _generate_cute_image("A Cat")
