import datetime
import logging
from typing import Annotated, Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from trail.database import database, user_table

logger = logging.getLogger(__name__)


pass_context = CryptContext(schemes=["bcrypt"])

SECRET_KEY = "134324"
ALGORITHM = "HS256"
oauth2_schema = OAuth2PasswordBearer(tokenUrl="token")


def access_token_expire_minutes() -> int:
    return 30


def confirm_token_expire_minutes() -> int:
    return 1440


def create_credential_exception(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def create_access_token(email: str):
    logger.info("Creating access token for user ", extra={"email": email})
    expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
        minutes=access_token_expire_minutes()
    )
    jwt_data = {"sub": email, "exp": expire, "type": "access"}
    encoded_jwt = jwt.encode(jwt_data, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_confirm_token(email: str):
    logger.info("Creating confirm token for user ", extra={"email": email})
    expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
        minutes=confirm_token_expire_minutes()
    )
    jwt_data = {"sub": email, "exp": expire, "type": "confirm"}
    encoded_jwt = jwt.encode(jwt_data, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_subject_for_token_type(token: str, type: Literal["access", "confirm"]) -> str:
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])

    except ExpiredSignatureError as e:
        raise create_credential_exception("token is expired") from e

    except JWTError as e:
        raise create_credential_exception("JWT error") from e

    email = payload.get("sub")

    if email is None:
        raise create_credential_exception("Email is not present")

    token_type = payload.get("type")

    if token_type is None or token_type != type:
        raise create_credential_exception("access type is not same")

    return email


def get_password_hash(password: str) -> str:
    return pass_context.hash(password)


def verify_password(plain_password: str, hash_password: str) -> bool:
    return pass_context.verify(plain_password, hash_password)


async def get_user(email: str):
    logger.info("fetching user from database", extra={"email": email})
    query = user_table.select().where(user_table.c.email == email)
    result = await database.fetch_one(query=query)

    if result:
        return result


async def authenticate_user(email: str, password: str):
    logger.info("Authenticating user", extra={"email": email})
    user = await get_user(email)
    if not user:
        raise create_credential_exception("User is not present")

    if not verify_password(password, user.password):
        raise create_credential_exception("password is not correct")

    if not user.confirmed:
        raise create_credential_exception("User not confirmed")
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_schema)]) -> dict:
    email = get_subject_for_token_type(token, "access")
    user = await get_user(email)

    if user is None:
        raise create_credential_exception("user is not found")

    return user
