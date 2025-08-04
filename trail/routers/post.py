import logging
from enum import Enum
from typing import Annotated

import sqlalchemy
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request

from trail.database import comment_table, database, like_table, post_table
from trail.model.post import (
    Comment,
    CommentIn,
    PostLike,
    PostLikeIn,
    PostLikeWithPost,
    UserPost,
    UserPostIn,
    UserPostWithComments,
)
from trail.model.user import User
from trail.security import get_current_user
from trail.tasks import generate_and_add_to_post

select_like_query = (
    sqlalchemy.select(post_table, sqlalchemy.func.count(like_table.c.id).label("likes"))
    .select_from(post_table.outerjoin(like_table))
    .group_by(post_table.c.id)
)
router = APIRouter()

logger = logging.getLogger(__name__)


async def find_post(post_id: int):
    query = post_table.select().where(post_table.c.id == post_id)
    return await database.fetch_one(query)


@router.post("/post", response_model=UserPost, status_code=201)
async def create_post(
    post: UserPostIn,
    CurrentUser: Annotated[User, Depends(get_current_user)],
    background_tasks: BackgroundTasks,
    request: Request,
    prompt: str = None,
):
    data = {**post.model_dump(), "user_id": CurrentUser.id}

    query = post_table.insert().values(data)

    last_record_id = await database.execute(query)

    if prompt:
        background_tasks.add_task(
            generate_and_add_to_post,
            last_record_id,
            request.url_for("get_post_with_comments", post_id=last_record_id),
            database,
            prompt,
        )

    return {**data, "id": last_record_id}


class PostSorting(str, Enum):
    new = "new"
    old = "old"
    most_likes = "most_likes"


@router.get("/post", response_model=list[PostLikeWithPost])
async def get_all_posts(sorting: PostSorting = PostSorting.new):
    logger.info("This is log inside get all post")
    if sorting == PostSorting.new:
        query = select_like_query.order_by(post_table.c.id.desc())
    elif sorting == PostSorting.old:
        query = select_like_query.order_by(post_table.c.id.asc())
    else:
        query = select_like_query.order_by(sqlalchemy.desc("likes"))
    logger.info(query)
    return await database.fetch_all(query)


@router.post("/comment", response_model=Comment, status_code=201)
async def create_comment(
    comment: CommentIn, CurrentUser: Annotated[User, Depends(get_current_user)]
):
    post_id = await find_post(comment.post_id)
    if not post_id:
        raise HTTPException(status_code=404, detail="No post present")
    data = {**comment.model_dump(), "user_id": CurrentUser.id}

    query = comment_table.insert().values(data)
    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}


@router.get("/post/{post_id}/comments", response_model=list[Comment])
async def get_comments_on_posts(post_id: int):
    query = comment_table.select().where(comment_table.c.post_id == post_id)
    return await database.fetch_all(query)


@router.get("/post/{post_id}", response_model=UserPostWithComments)
async def get_post_with_comments(post_id: int):
    query = select_like_query.where(post_table.c.id == post_id)

    post = await database.fetch_one(query)

    if not post:
        raise HTTPException(status_code=404, detail="Post not present")

    return {
        "post": post,
        "comments": await get_comments_on_posts(post_id),
    }


@router.post("/like", response_model=PostLike, status_code=201)
async def post_like(
    like: PostLikeIn, CurrentUser: Annotated[User, Depends(get_current_user)]
):
    post = await find_post(like.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not present")

    data = {**like.model_dump(), "user_id": CurrentUser.id}
    query = like_table.insert().values(data)
    like_id = await database.execute(query)
    return {**data, "id": like_id}
