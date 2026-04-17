from fastapi import APIRouter

from app.api.routes.accounts import router as accounts_router
from app.api.routes.trades import router as trades_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(accounts_router)
api_router.include_router(trades_router)
