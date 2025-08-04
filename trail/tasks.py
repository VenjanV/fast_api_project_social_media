import logging
from json.decoder import JSONDecodeError

import httpx
from databases import Database

from trail.config import config
from trail.database import post_table

logger = logging.getLogger(__name__)


class APIResponseError(Exception):
    pass


async def _generate_cute_image(prompt: str):
    logger.info("Generating image")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "url",
                data={"text": prompt},
                headers={"api-key": config.DEEP_AI_API_KEY},
            )
            logger.info(response)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as er:
            raise APIResponseError(
                f"api request failed with status code {er.response.status_code}"
            ) from er
        except (JSONDecodeError, TypeError) as er:
            raise APIResponseError(f"api request parsing failed {er}") from er


async def generate_and_add_to_post(
    post_id: int,
    post_url: str,
    database: Database,
    prompt: str = "A cat sitting near chair",
):
    try:
        response = await _generate_cute_image(prompt)
    except httpx.HTTPStatusError:
        raise APIResponseError("API didn't send any response")

    logger.info(response)
    query = (
        post_table.update()
        .where(post_table.c.id == post_id)
        .values(url_link=response["output_url"])
    )
    logger.info(query)

    await database.execute(query)
    logger.info("Completed database execution")
    return response
