import logging

from fastapi import APIRouter, HTTPException, status

from trail.database import database, user_table
from trail.model.user import UserIn
from trail.security import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_user,
)

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/register", status_code=201)
async def register(user: UserIn):
    if await get_user(user.email):
        raise HTTPException(
            detail="The user already exist",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    password = get_password_hash(user.password)
    query = user_table.insert().values(email=user.email, password=password)

    logger.info(query)

    await database.execute(query)
    return {"detail": "User Created"}


@router.post("/token")
async def login(user: UserIn):
    user = await authenticate_user(user.email, user.password)
    token = create_access_token(user.email)
    return {"access_token": token, "token_type": "bearer"}
