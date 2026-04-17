from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core import state
from app.core.config import get_settings
from app.services.ctrader import CTraderGateway
from app.services.exceptions import CTraderApiError, CTraderServiceError, CTraderTimeoutError


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    gateway = CTraderGateway(settings)
    gateway.start()
    state.gateway = gateway
    try:
        yield
    finally:
        state.gateway = None
        gateway.stop()


app = FastAPI(
    title=get_settings().app_name,
    version=get_settings().app_version,
    lifespan=lifespan,
)
app.include_router(api_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(CTraderTimeoutError)
async def ctrader_timeout_handler(_request: Request, exc: CTraderTimeoutError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content={"detail": str(exc)},
    )


@app.exception_handler(CTraderApiError)
async def ctrader_api_handler(_request: Request, exc: CTraderApiError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": {"code": exc.code, "description": exc.description}},
    )


@app.exception_handler(CTraderServiceError)
async def ctrader_service_handler(_request: Request, exc: CTraderServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
    )
