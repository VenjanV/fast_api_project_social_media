import logging
from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.exception_handlers import http_exception_handler

from trail.database import database
from trail.logging_config import Config_logger
from trail.routers.post import router as post_router
from trail.routers.user import router as user_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Config_logger()
    await database.connect()
    yield
    await database.disconnect()


app = FastAPI(lifespan=lifespan)

app.include_router(post_router)
app.include_router(user_router)
app.add_middleware(CorrelationIdMiddleware)


@app.exception_handler(HTTPException)
async def http_exception_handler_logging(request, exc):
    logger.error(f"There is error {exc.status_code}, {exc.detail}")
    return await http_exception_handler(request, exc)
