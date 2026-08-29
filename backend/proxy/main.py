from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.proxy.routes import ProxyAPI

proxy = ProxyAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await proxy.aclose()


app = FastAPI(
    title="evmbench-proxy",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.include_router(proxy.router)
