import logging

from fastapi import APIRouter, HTTPException, Request, status

from trail.database import database, user_table
from trail.model.user import UserIn
from trail.security import (
    authenticate_user,
    create_access_token,
    create_confirm_token,
    get_password_hash,
    get_subject_for_token_type,
    get_user,
)

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/register", status_code=201)
async def register(user: UserIn, request: Request):
    if await get_user(user.email):
        raise HTTPException(
            detail="The user already exist",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    password = get_password_hash(user.password)
    query = user_table.insert().values(email=user.email, password=password)

    logger.info(query)

    await database.execute(query)
    # return {"detail": "User Created"}
    return {
        "detail": "User created, click on the link to confirm user",
        "confirmation_url": request.url_for(
            "confirm_email", token=create_confirm_token(user.email)
        ),
    }


@router.post("/token")
async def login(user: UserIn):
    user = await authenticate_user(user.email, user.password)
    token = create_access_token(user.email)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/confirm/{token}")
async def confirm_email(token: str):
    email = get_subject_for_token_type(token, "confirm")
    query = (
        user_table.update().where(user_table.c.email == email).values(confirmed=True)
    )
    logger.info("Updating the status of the email confirmation")
    await database.execute(query)
    return {"detail": "Email Confirmed"}
