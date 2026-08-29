import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api.routes import HealthAPI, JobsAPI
from backend.database.db import Database

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create the tables if they are not there. Every statement in
    # table.sql is IF NOT EXISTS, so this is safe on every start.
    Database().init_schema()
    log.info("schema ready")
    yield


# /docs and /openapi.json describe every endpoint. The untrusted worker
# can reach our network, so do not hand it a map in production.
DEBUG = os.getenv("DEBUG", "").lower() in {"1", "true", "yes"}

app = FastAPI(
    title="evmbench",
    lifespan=lifespan,
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
    openapi_url="/openapi.json" if DEBUG else None,
)

app.include_router(HealthAPI().router)
app.include_router(JobsAPI().router)
